import {action, computed, observable} from 'mobx';
import React, {Context} from "react";
import {Media} from "../types";
import {sumMediaSize} from "../util";
import {deleteMedia, ignoreMedia} from "../util/api";
import {newMovieStoreContext} from "./ContentStore";

export class MediaStore {
  @observable.deep
  media: Record<number, Media> = {};

  @observable isDeleting = false;

  @action
  addMedia(media: Media) {
    this.media[media.id] = media;
  }

  @action
  removeMedia(media: Media) {
    delete this.media[media.id];
  }

  @action
  reset() {
    this.media = {};
  }

  deleteMedia(libraryName: string, movieKey: string, media: Media): Promise<any> {
    return new Promise((resolve, reject) => {
      deleteMedia(libraryName, movieKey, media.id)
        .then(() => {
          this.removeMedia(media);
          resolve();
        }).catch((error) => {
          reject(error);
        });
    })
  }

  @computed
  get length(): number {
    return Object.keys(this.media).length;
  }

  @computed
  get totalSizeBytes(): number {
    let total = 0;
    Object.values(this.media).forEach(media => {
      total += sumMediaSize(media);
    });
    return total;
  }
}

export function newMediaStore(): MediaStore {
  return new MediaStore();
}

export function newMediaStoreContext(): Context<MediaStore> {
  return React.createContext<MediaStore>(newMediaStore());
}

export const movieContext = newMovieStoreContext();
export const mediaContext = newMediaStoreContext();
export const deletedMediaContext = newMediaStoreContext();
