import axios from 'axios';
import {action, computed, observable} from "mobx";
import React, {Context} from "react";
import {Movie} from "../types";

export class MovieStore {
  @observable.deep
  movies: Movie[] = [];

  @observable
  loading: boolean = false;

  @observable
  loadingFailed: boolean = false;

  @computed
  get length(): number {
    return this.movies.length;
  }

  @action
  setMovies(movies: Movie[]) {
    this.movies = movies;
  }

  loadMovies(url: string): void {
    this.loading = true;
    this.loadingFailed = false;
    this.setMovies([]);
    axios.get(url).then(result => {
      this.setMovies(result.data);
      this.loading = false;
    }).catch(() => {
      this.loading = false;
      this.loadingFailed = true;
    });
  }

  loadDupeMovies(): void {
    const url = "http://localhost:5000/movies/dupes";
    this.loadMovies(url);
  }

  loadSampleMovies(): void {
    const url = "http://localhost:5000/movies/samples";
    this.loadMovies(url);
  }
}

export function newMovieStore(): MovieStore {
  return new MovieStore();
}

export function newMovieStoreContext(): Context<MovieStore> {
  return React.createContext<MovieStore>(newMovieStore());
}
