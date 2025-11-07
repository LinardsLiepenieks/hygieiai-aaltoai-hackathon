// hooks/useTextToSpeech.ts
import { useRef, useState, useCallback } from 'react';

type TTSStatus = 'idle' | 'loading' | 'playing' | 'error' | 'done';

export default function useTextToSpeech() {
  const [status, setStatus] = useState<TTSStatus>('idle');
  const [error, setError] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const controllerRef = useRef<AbortController | null>(null);

  const ELEVENLABS_API_KEY = process.env.NEXT_PUBLIC_ELEVENLABS_API_KEY ?? '';
  const hasApiKey = Boolean(
    ELEVENLABS_API_KEY && !ELEVENLABS_API_KEY.includes('YOUR')
  );

  // Default voice (you can change or make it configurable)
  const VOICE_ID = '21m00Tcm4TlvDq8ikWAM'; // Rachel (premier voice)

  const speak = useCallback(
    async (text: string, voiceId?: string) => {
      if (!hasApiKey) {
        setError('Missing ElevenLabs API key');
        setStatus('error');
        return;
      }

      if (!text.trim()) {
        setError('No text to speak');
        setStatus('error');
        return;
      }

      // Cancel any ongoing request
      if (controllerRef.current) {
        controllerRef.current.abort();
      }

      const controller = new AbortController();
      controllerRef.current = controller;

      setStatus('loading');
      setError(null);

      try {
        const res = await fetch(
          `https://api.elevenlabs.io/v1/text-to-speech/${
            voiceId || VOICE_ID
          }/stream`,
          {
            method: 'POST',
            headers: {
              'xi-api-key': ELEVENLABS_API_KEY,
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              text: text.trim(),
              model_id: 'eleven_turbo_v2_5', // Fastest + high quality
              voice_settings: {
                stability: 0.5,
                similarity_boost: 0.75,
                style: 0.5,
                use_speaker_boost: true,
              },
              // Optional: Add SSML
              // pronunciation_dictionary_locators: [],
            }),
            signal: controller.signal,
          }
        );

        if (!res.ok) {
          const err = await res.text();
          throw new Error(err || 'TTS request failed');
        }

        if (!res.body) throw new Error('No audio stream');

        // Create blob URL from stream
        const blob = await new Response(res.body).blob();
        const url = URL.createObjectURL(blob);

        // Cleanup old audio
        if (audioRef.current) {
          audioRef.current.pause();
          URL.revokeObjectURL(audioRef.current.src);
          audioRef.current = null;
        }

        const audio = new Audio(url);
        audioRef.current = audio;

        audio.onplay = () => setStatus('playing');
        audio.onended = () => {
          setStatus('done');
          setTimeout(() => setStatus('idle'), 2000);
        };
        audio.onerror = () => {
          setError('Audio playback failed');
          setStatus('error');
        };

        await audio.play();
      } catch (err: any) {
        if (err.name === 'AbortError') return;
        console.error('TTS Error:', err);
        setError(err.message || 'Failed to generate speech');
        setStatus('error');
      }
    },
    [hasApiKey]
  );

  const stop = useCallback(() => {
    if (controllerRef.current) {
      controllerRef.current.abort();
      controllerRef.current = null;
    }
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      URL.revokeObjectURL(audioRef.current.src);
      audioRef.current = null;
    }
    setStatus('idle');
  }, []);

  const pause = useCallback(() => {
    audioRef.current?.pause();
    setStatus('idle');
  }, []);

  const resume = useCallback(() => {
    audioRef.current?.play();
    setStatus('playing');
  }, []);

  // Cleanup on unmount
  const cleanup = useCallback(() => {
    stop();
  }, [stop]);

  return {
    speak,
    stop,
    pause,
    resume,
    cleanup,
    status,
    error,
    isLoading: status === 'loading',
    isPlaying: status === 'playing',
    isIdle: status === 'idle',
    isError: status === 'error',
    hasApiKey,
  };
}
