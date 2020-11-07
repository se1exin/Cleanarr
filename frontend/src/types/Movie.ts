import {Media} from "./Media";

export interface Movie {
  addedAt: string,
  key: string,
  lastViewedAt: string,
  librarySectionID: string,
  summary: string,
  thumb: string,
  title: string,
  titleSort: string,
  type: number,
  updatedAt: string,
  viewCount: number,
  duration: number,
  guid: string,
  originalTitle: string,
  originallyAvailableAt: string,
  rating: number,
  ratingImage: string,
  studio: string,
  tagline: string,
  userRating: number,
  year: number,
  media: Media[],
  library: string
}
