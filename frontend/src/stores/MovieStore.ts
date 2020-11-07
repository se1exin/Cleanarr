import {action, computed, observable} from "mobx";
import React, {Context} from "react";
import {Movie} from "../types";
import {getDupeMovies, getSampleMovies} from "../util/api";

export class MovieStore {
  @observable.deep
  movies: Movie[] = [];

  @observable
  loading: boolean = false;

  @observable
  loadingFailed: boolean = false;

  @observable
  loadingError: Error|null = null

  @computed
  get length(): number {
    return this.movies.length;
  }

  @action
  setMovies(movies: Movie[]) {
    this.movies = movies;
  }

  loadMovies(handlerFn: () => Promise<any>): void {
    this.loading = true;
    this.loadingFailed = false;
    this.loadingError = null;
    this.setMovies([]);
    handlerFn().then(result => {
      this.setMovies(result.data);
      this.loading = false;
    }).catch((error) => {

      this.loading = false;
      this.loadingFailed = true;

      if (error.response?.data?.error) {
        this.loadingError = new Error(error.response?.data?.error);
      }
    });
  }

  loadDupeMovies(): void {
    this.loadMovies(getDupeMovies);
  }

  loadSampleMovies(): void {
    this.loadMovies(getSampleMovies);
  }
}

export function newMovieStore(): MovieStore {
  return new MovieStore();
}

export function newMovieStoreContext(): Context<MovieStore> {
  return React.createContext<MovieStore>(newMovieStore());
}
