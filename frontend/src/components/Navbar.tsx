interface NavbarProps {
  onCallClick?: () => void;
  hasNotification?: boolean;
}

export default function Navbar({
  onCallClick,
  hasNotification = true,
}: NavbarProps) {
  return (
    <nav className="bg-gradient-to-r from-blue-600 via-blue-700 to-blue-800 text-white shadow-lg">
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex flex-col">
              <h1 className="text-2xl font-bold tracking-tight">
                Futuuri: Hygiei AI
              </h1>
              <p className="text-xs text-blue-200 font-medium">
                (Llama 3.3 and ElevenLabs Scribe, deployed on Datacrunch)
              </p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            {/* Call Button with Notification */}
            <button
              onClick={onCallClick}
              className="relative h-10 w-10 rounded-full bg-blue-500 hover:bg-blue-400 flex items-center justify-center transition-all shadow-inner"
              aria-label="Toggle call sidebar"
            >
              {/* Phone Icon */}
              <svg
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth={2}
                stroke="currentColor"
                className="w-5 h-5"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M2.25 6.75c0 8.284 6.716 15 15 15h2.25a2.25 2.25 0 002.25-2.25v-1.372c0-.516-.351-.966-.852-1.091l-4.423-1.106c-.44-.11-.902.055-1.173.417l-.97 1.293c-.282.376-.769.542-1.21.38a12.035 12.035 0 01-7.143-7.143c-.162-.441.004-.928.38-1.21l1.293-.97c.363-.271.527-.734.417-1.173L6.963 3.102a1.125 1.125 0 00-1.091-.852H4.5A2.25 2.25 0 002.25 4.5v2.25z"
                />
              </svg>

              {/* Notification Badge */}
              {hasNotification && (
                <span className="absolute -top-1 -right-1 h-4 w-4 bg-red-500 rounded-full border-2 border-blue-800 flex items-center justify-center">
                  <span className="text-[10px] font-bold">1</span>
                </span>
              )}
            </button>

            <div className="h-10 w-10 rounded-full bg-blue-500 flex items-center justify-center text-sm font-semibold shadow-inner">
              AI
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
}
