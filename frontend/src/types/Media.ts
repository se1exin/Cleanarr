import {MediaPart} from "./MediaPart";

export interface Media {
  id: number,
  aspectRatio: number,
  audioChannels: number,
  audioCodec: string,
  bitrate: number,
  container: string,
  duration: number,
  width: number,
  height: number,
  has64bitOffsets?: boolean,
  optimizedForStreaming?: boolean,
  target?: string,
  title?: string,
  videoCodec: string,
  videoFrameRate: string,
  videoProfile: string,
  videoResolution: string,
  parts: MediaPart[]
}
