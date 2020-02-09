/**
 * Helpful Utilities
 */
import {Media} from "../types";

/**
 * Total size of all Parts in a given copy of Media
 * @param media
 * @return total size in bytes
 */
export const sumMediaSize = (media: Media): number => {
  return media.parts
    .map(value => value.size)
    .reduce((sum, x) => (sum + x))
};

/**
 * Bytes to a human readable string
 * @param bytes
 */
export const bytesToSize = (bytes: number): string => {
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  if (bytes === 0) return 'n/a';
  const i = parseInt(String(Math.floor(Math.log(bytes) / Math.log(1024))), 10);
  if (i === 0) return `${bytes} ${sizes[i]}`;
  return `${(bytes / (1024 ** i)).toFixed(1)} ${sizes[i]}`;
};
