export {};

declare global {
  interface Window {
    electronAPI: {
      resizeWindow: (width: number, height: number) => void;
    };
  }
}