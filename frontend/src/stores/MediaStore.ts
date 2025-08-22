import { action, computed, observable } from 'mobx'
import React, { Context } from 'react'
import { Media } from '../types'
import { sumMediaSize } from '../util'
import { deleteMedia, deleteMediaBatch } from '../util/api'

export class MediaStore {
  @observable.deep
  media: Record<number, Media> = {}

  @observable isDeleting = false
  @observable deleteErrors: Record<number, string> = {}

  @action
  addMedia(media: Media) {
    this.media[media.id] = media
    // Clear any previous errors for this media
    delete this.deleteErrors[media.id]
  }

  @action
  removeMedia(media: Media) {
    delete this.media[media.id]
    // Clear any errors for this media
    delete this.deleteErrors[media.id]
  }

  @action
  reset() {
    this.media = {}
    this.deleteErrors = {}
  }

  @action
  setDeleteError(mediaId: number, error: string) {
    this.deleteErrors[mediaId] = error
  }

  @action
  clearDeleteError(mediaId: number) {
    delete this.deleteErrors[mediaId]
  }

  async deleteMedia(libraryName: string, movieKey: string, media: Media): Promise<any> {
    try {
      this.isDeleting = true
      this.clearDeleteError(media.id)

      console.log(`Deleting media ${media.id} from library ${libraryName}`)

      const result = await deleteMedia(libraryName, movieKey, media.id)

      if (result.data.success) {
        this.removeMedia(media)
        console.log(`Successfully deleted media ${media.id}`)
        return result
      } else {
        const errorMsg = result.data.error || 'Delete operation failed'
        this.setDeleteError(media.id, errorMsg)
        throw new Error(errorMsg)
      }
    } catch (error: any) {
      const errorMsg = error.response?.data?.error || error.message || 'Delete operation failed'
      this.setDeleteError(media.id, errorMsg)
      console.error(`Failed to delete media ${media.id}:`, errorMsg)
      throw error
    } finally {
      this.isDeleting = false
    }
  }

  async deleteMediaBatch(
    items: Array<{ libraryName: string; movieKey: string; media: Media }>,
    batchSize: number = 10
  ): Promise<{ success: number; failed: number; errors: Array<{ mediaId: number; error: string }> }> {
    try {
      this.isDeleting = true
      console.log(`Starting batch delete of ${items.length} items in batches of ${batchSize}`)

      // Clear all errors for items being processed
      items.forEach(item => this.clearDeleteError(item.media.id))

      const result = await deleteMediaBatch(
        items.map(item => ({
          library: item.libraryName,
          contentKey: item.movieKey,
          media: item.media
        })),
        batchSize
      )

      // Remove successfully deleted items from the store
      items.forEach(item => {
        if (!result.errors.some(error => error.mediaId === item.media.id)) {
          this.removeMedia(item.media)
        }
      })

      // Set errors for failed items
      result.errors.forEach(error => {
        this.setDeleteError(error.mediaId, error.error)
      })

      console.log(`Batch delete completed: ${result.success} successful, ${result.failed} failed`)
      return result

    } catch (error: any) {
      console.error('Batch delete failed:', error)
      throw error
    } finally {
      this.isDeleting = false
    }
  }

  @computed
  get length(): number {
    return Object.keys(this.media).length
  }

  @computed
  get totalSizeBytes(): number {
    let total = 0
    Object.values(this.media).forEach((media) => {
      total += sumMediaSize(media)
    })
    return total
  }

  @computed
  get hasErrors(): boolean {
    return Object.keys(this.deleteErrors).length > 0
  }

  @computed
  get errorCount(): number {
    return Object.keys(this.deleteErrors).length
  }
}

export function newMediaStore(): MediaStore {
  return new MediaStore()
}

export function newMediaStoreContext(): Context<MediaStore> {
  return React.createContext<MediaStore>(newMediaStore())
}

export const mediaContext = newMediaStoreContext()
export const deletedMediaContext = newMediaStoreContext()
