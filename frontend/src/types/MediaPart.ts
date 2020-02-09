import {MediaPartStream} from "./MediaPartStream";

export interface MediaPart {
  id: number,
  container: string,
  duration: number,
  file: string,
  exists:boolean,
  indexes?: any,
  key: string,
  size: number,
  streams: MediaPartStream[]
}
