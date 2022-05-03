import {action, computed, observable} from "mobx";
import React, {Context} from "react";
import {Content} from "../types";
import {getDupeContent, getSampleContent, ignoreMedia} from "../util/api";

export class ContentStore {
  @observable.deep
  content: Content[] = [];

  @observable
  loading: boolean = false;

  @observable
  loadingFailed: boolean = false;

  @observable
  loadingError: Error|null = null

  @computed
  get length(): number {
    return this.content.length;
  }

  @action
  setContent(movies: Content[]) {
    this.content = movies;
  }

  loadContent(handlerFn: () => Promise<any>): void {
    this.loading = true;
    this.loadingFailed = false;
    this.loadingError = null;
    this.setContent([]);
    handlerFn().then(result => {
      this.setContent(result.data);
      this.loading = false;
    }).catch((error) => {

      this.loading = false;
      this.loadingFailed = true;

      if (error.response?.data?.error) {
        this.loadingError = new Error(error.response?.data?.error);
      }
    });
  }

  ignoreContent(contentKey: string): Promise<any> {
    return new Promise((resolve, reject) => {
      ignoreMedia(contentKey)
          .then(() => {
            resolve();
          }).catch((error) => {
        reject(error);
      });
    })
  }


  loadDupeContent(): void {
    this.loadContent(getDupeContent);
  }

  loadSampleMovies(): void {
    this.loadContent(getSampleContent);
  }
}

export function newContentStore(): ContentStore {
  return new ContentStore();
}

export function newMovieStoreContext(): Context<ContentStore> {
  return React.createContext<ContentStore>(newContentStore());
}
