import { action, computed, observable, runInAction, makeObservable } from 'mobx'
import React, { Context } from 'react'
import { Content } from '../types'
import { getDupeContent, getSampleContent, ignoreMedia, unIgnoreMedia } from '../util/api'

export const PAGE_SIZE: number = Number(process.env.REACT_APP_PAGE_SIZE) || 10

export class ContentStore {
  content: Content[] = []
  loading: boolean = false
  loadingFailed: boolean = false
  loadingError: Error | null = null
  includeIgnored: boolean = false

  constructor() {
    makeObservable(this, {
      content: observable,
      loading: observable,
      loadingFailed: observable,
      loadingError: observable,
      includeIgnored: observable,
      items: computed,
      ignoredItems: computed,
      length: computed,
      setContent: action,
      setIncludeIgnore: action,
      loadContent: action,
      ignoreContent: action,
      unIgnoreContent: action,
      loadDupeContent: action,
      loadSampleMovies: action,
    })
  }

  @computed
  get items(): Content[] {
    // Temporarily bypass the ignored filter to debug the issue
    console.log('ContentStore.items called:')
    console.log('  this.content.length:', this.content.length)
    console.log('  this.includeIgnored:', this.includeIgnored)
    console.log('  this.content:', this.content)
    console.log('  this.content reference:', this.content)
    console.log('  Array.isArray(this.content):', Array.isArray(this.content))

    // Always return all content for now
    return this.content

    // Original logic (commented out for debugging):
    // if (this.includeIgnored) {
    //   return this.content
    // }
    // return this.content.filter((item) => !item.ignored)
  }

  @computed
  get ignoredItems(): Content[] {
    return this.content.filter((item) => !!item.ignored)
  }

  @computed
  get length(): number {
    return this.items.length
  }

  @action
  setContent(movies: Content[]) {
    console.log('setContent called with:', movies)
    console.log('Previous content length:', this.content.length)

    // Clear the array first
    this.content.length = 0
    // Push all items to maintain reactivity
    movies.forEach((movie) => this.content.push(movie))

    console.log('New content length:', this.content.length)
    console.log('Content array reference changed:', this.content === movies)

    // Force a MobX reaction by accessing the items property
    console.log('Forcing MobX reaction by accessing items...')
    const currentItems = this.items
    console.log('Items after setContent:', currentItems.length)
  }

  @action
  setIncludeIgnore(value: boolean) {
    this.includeIgnored = value
  }

  loadContent(handlerFn: () => Promise<any>): void {
    this.loading = true
    this.loadingFailed = false
    this.loadingError = null
    this.setContent([])
    handlerFn()
      .then((result) => {
        this.setContent(result.data)
        this.loading = false
      })
      .catch((error) => {
        this.loading = false
        this.loadingFailed = true

        if (error.response?.data?.error) {
          this.loadingError = new Error(error.response?.data?.error)
        }
      })
  }

  @action
  async ignoreContent(contentKey: string): Promise<any> {
    return new Promise<void>((resolve, reject) => {
      ignoreMedia(contentKey)
        .then(() => {
          for (let i = 0; i < this.content.length; i++) {
            if (this.content[i].key === contentKey) {
              const item = {
                ...this.content[i],
                ignored: true,
              }
              runInAction(() => {
                console.log(item)
                this.content.splice(i, 1, item)
              })
              break
            }
          }
          resolve()
        })
        .catch((error) => {
          reject(error)
        })
    })
  }

  @action
  async unIgnoreContent(contentKey: string): Promise<any> {
    return new Promise<void>((resolve, reject) => {
      unIgnoreMedia(contentKey)
        .then(() => {
          for (let i = 0; i < this.content.length; i++) {
            if (this.content[i].key === contentKey) {
              const item = {
                ...this.content[i],
                ignored: false,
              }
              runInAction(() => {
                console.log(item)
                this.content.splice(i, 1, item)
              })
              break
            }
          }
          resolve()
        })
        .catch((error) => {
          reject(error)
        })
    })
  }

  loadDupeContent(): void {
    // Single API call to get all duplicates
    console.log('loadDupeContent called - starting...')
    this.loading = true
    this.loadingFailed = false
    this.loadingError = null
    this.setContent([])

    getDupeContent()
      .then((result) => {
        console.log('loadDupeContent success - result:', result)
        console.log('result.data:', result.data)
        console.log('Setting content with length:', result.data?.data?.length || 0)
        this.setContent(result.data.data) // Fix: access the nested data array
        this.loading = false
        console.log('Content set, loading = false')
      })
      .catch((error) => {
        console.error('loadDupeContent error:', error)
        this.loading = false
        this.loadingFailed = true
        if (error.response?.data?.error) {
          this.loadingError = new Error(error.response?.data?.error)
        }
      })
  }

  loadSampleMovies(): void {
    this.loadContent(getSampleContent)
  }
}

export function newContentStore(): ContentStore {
  return new ContentStore()
}

export function newContentStoreContext(): Context<ContentStore> {
  return React.createContext<ContentStore>(newContentStore())
}

export const contentContext = newContentStoreContext()
