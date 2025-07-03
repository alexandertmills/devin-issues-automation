import React, { useRef, useEffect } from 'react';

interface CowbellPlayerProps {
  shouldPlay: boolean;
  onPlayComplete?: () => void;
}

export const CowbellPlayer: React.FC<CowbellPlayerProps> = ({ 
  shouldPlay, 
  onPlayComplete 
}) => {
  const audioRef = useRef<HTMLAudioElement>(null);

  useEffect(() => {
    if (shouldPlay && audioRef.current) {
      audioRef.current.play().catch(error => {
        console.log('Audio play failed (user interaction required):', error);
      });
    }
  }, [shouldPlay]);

  const handleEnded = () => {
    if (onPlayComplete) {
      onPlayComplete();
    }
  };

  return (
    <audio
      ref={audioRef}
      preload="auto"
      onEnded={handleEnded}
      style={{ display: 'none' }}
    >
      <source src="/cowbell.wav" type="audio/wav" />
      Your browser does not support the audio element.
    </audio>
  );
};
