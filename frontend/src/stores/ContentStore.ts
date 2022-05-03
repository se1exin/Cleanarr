import {action, computed, observable, runInAction} from "mobx";
import React, {Context} from "react";
import {Content} from "../types";
import {getDupeContent, getSampleContent, ignoreMedia, unIgnoreMedia} from "../util/api";

export class ContentStore {
  @observable.deep
  content: Content[] = [];

  @observable
  loading: boolean = false;

  @observable
  loadingFailed: boolean = false;

  @observable
  loadingError: Error|null = null;

  @observable
  includeIgnored: boolean = false;

  @computed
  get items(): Content[] {
    if (this.includeIgnored) {
      return this.content;
    }
    return this.content.filter(item => !item.ignored);
  }

  @computed
  get ignoredItems(): Content[] {
    return this.content.filter(item => !!item.ignored);
  }

  @computed
  get length(): number {
    return this.items.length;
  }

  @action
  setContent(movies: Content[]) {
    this.content = movies
  }

  @action
  setIncludeIgnore(value: boolean) {
    this.includeIgnored = value;
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

  @action
  async ignoreContent(contentKey: string): Promise<any> {
    return new Promise((resolve, reject) => {
      ignoreMedia(contentKey)
          .then(() => {
            for (let i = 0; i < this.content.length; i++) {
              if (this.content[i].key === contentKey) {
                const item = {
                  ...this.content[i],
                  ignored: true,
                }
                runInAction(() => {
                  console.log(item);
                  this.content.splice(i, 1, item);
                });
                break;
              }
            }
            resolve();
          }).catch((error) => {
        reject(error);
      });
    })
  }

  @action
  async unIgnoreContent(contentKey: string): Promise<any> {
    return new Promise((resolve, reject) => {
      unIgnoreMedia(contentKey)
        .then(() => {
          for (let i = 0; i < this.content.length; i++) {
            if (this.content[i].key === contentKey) {
              const item = {
                ...this.content[i],
                ignored: false,
              }
              runInAction(() => {
                console.log(item);
                this.content.splice(i, 1, item);
              });
              break;
            }
          }
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

export function newContentStoreContext(): Context<ContentStore> {
  return React.createContext<ContentStore>(newContentStore());
}

export const contentContext = newContentStoreContext();
