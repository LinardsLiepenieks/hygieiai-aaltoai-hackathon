import { useEffect, useRef, useState } from 'react';

type SetText = (value: React.SetStateAction<string>) => void;

export default function useRecording(setText: SetText) {
  const [status, setStatus] = useState<string>('Ready - Tap mic to speak');
  const [isRecording, setIsRecording] = useState(false);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);

  const ELEVENLABS_API_KEY = process.env.NEXT_PUBLIC_ELEVENLABS_API_KEY ?? '';
  const hasApiKey = Boolean(
    ELEVENLABS_API_KEY && !ELEVENLABS_API_KEY.includes('YOUR')
  );

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
      }
    };
  }, []);

  const preventDefault = (e: React.MouseEvent | React.TouchEvent) => {
    e.preventDefault();
  };

  const uploadAndTranscribe = async (blob: Blob) => {
    const formData = new FormData();
    formData.append('file', blob, 'recording.webm');
    formData.append('model_id', 'scribe_v1');
    formData.append('language_code', 'en');
    formData.append('diarize', 'true');

    try {
      const res = await fetch('https://api.elevenlabs.io/v1/speech-to-text', {
        method: 'POST',
        headers: { 'xi-api-key': ELEVENLABS_API_KEY },
        body: formData,
      });

      if (!res.ok) {
        const error = await res.text();
        throw new Error(error || 'Upload failed');
      }

      const { transcription_id } = await res.json();
      setStatus('Transcribing…');
      pollTranscript(transcription_id);
    } catch (err: any) {
      setStatus('Upload failed: ' + err.message);
      setIsRecording(false);
    }
  };

  const pollTranscript = async (id: string) => {
    let attempts = 0;
    const maxAttempts = 40;

    const check = async () => {
      attempts++;
      try {
        const res = await fetch(
          `https://api.elevenlabs.io/v1/speech-to-text/transcripts/${id}`,
          { headers: { 'xi-api-key': ELEVENLABS_API_KEY } }
        );

        if (!res.ok) throw new Error('Failed to fetch transcript');

        const data = await res.json();

        if (data.text) {
          const t = data.text.trim();
          setText((prev) => (prev ? prev + ' ' + t : t));
          setStatus(
            `Transcribed! (${data.words?.length || t.split(' ').length} words)`
          );
          return;
        }

        if (attempts >= maxAttempts) {
          setStatus('Timeout – try shorter clip');
          return;
        }

        setStatus(`Transcribing… (${(attempts * 1.5).toFixed(1)}s)`);
        setTimeout(check, 1500);
      } catch (err) {
        setStatus('Error fetching transcript');
      }
    };

    check();
  };

  const toggleRecording = async (e: React.MouseEvent | React.TouchEvent) => {
    e.preventDefault();

    if (!hasApiKey) {
      setStatus('Error: Add your ElevenLabs API key in .env.local');
      return;
    }

    if (isRecording) {
      // === STOP RECORDING ===
      if (mediaRecorderRef.current?.state === 'recording') {
        mediaRecorderRef.current.stop();
        setStatus('Processing recording…');
      }
      return;
    }

    // === START RECORDING ===
    // Clean up any old stream
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => {
        t.stop();
        t.enabled = false;
      });
      streamRef.current = null;
    }

    audioChunksRef.current = [];
    setStatus('Recording… tap again to stop');
    setIsRecording(true);

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 48000,
        },
      });

      streamRef.current = stream;

      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : 'audio/webm';

      const mediaRecorder = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const blob = new Blob(audioChunksRef.current, { type: mimeType });
        await uploadAndTranscribe(blob);

        // Full cleanup
        if (streamRef.current) {
          streamRef.current.getTracks().forEach((t) => {
            t.stop();
            t.enabled = false;
          });
          streamRef.current = null;
        }

        mediaRecorderRef.current = null;
        setIsRecording(false);
        setStatus('Ready - Tap mic to speak');
      };

      mediaRecorder.start();
      setStatus('Recording… tap again to stop');
    } catch (err: any) {
      console.error('Microphone error:', err);
      setStatus('Mic access denied');
      setIsRecording(false);
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
        streamRef.current = null;
      }
    }
  };

  return {
    status,
    isRecording,
    preventDefault,
    toggleRecording,
    hasApiKey,
    setStatus,
  };
}
