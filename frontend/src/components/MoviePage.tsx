import {majorScale, Pane, toaster} from "evergreen-ui";
import {autorun} from "mobx";
import {Observer} from "mobx-react-lite";
import React, {FunctionComponent, useEffect, useState} from 'react';
import {newMediaStoreContext} from "../stores/MediaStore";
import {newMovieStoreContext} from "../stores/MovieStore";
import {Media, Movie} from "../types";
import {bytesToSize, sumMediaSize} from "../util";
import {MovieItem} from "./MovieItem";
import {MovieList} from "./MovieList";
import {MovieTopBar} from "./MovieTopBar";

export const MoviePage:FunctionComponent<any> = () => {

  const listingTypes = [
    {
      label: 'Duplicates',
      value: 'duplicate'
    },
    {
      label: 'Samples',
      value: 'sample'
    },
  ];

  const [listingType, setListingType] = useState(listingTypes[0].value);

  const movieStore = React.useContext(newMovieStoreContext());
  const mediaStore = React.useContext(newMediaStoreContext());
  const deletedMediaStore = React.useContext(newMediaStoreContext());

  useEffect(() => {
    onRefresh();
  });

  useEffect(() => {
    // Determine the default media items to be removed
    autorun(() => {
      movieStore.movies.forEach((movie: Movie) => {
        let _media = [
          ...movie.media
        ];
        let sortedMedia = _media
          .sort((a, b) => {
            const aSize = sumMediaSize(a);
            const bSize = sumMediaSize(b);
            if (aSize < bSize) return 1;
            if (aSize > bSize) return -1;
            return 0;
          })
          .sort((a, b) => {
            if (a.width < b.width) return 1;
            if (a.width > b.width) return -1;
            return 0;
          });

        // Remove the top entry and then select/check (for removal) the rest
        sortedMedia.forEach(((media, index) => {
          if (index !== 0) {
            mediaStore.addMedia(media);
          }
        }));
      });
    });
  }, [mediaStore, mediaStore.media, movieStore.movies]);

  const onListingTypeChange = (listingType: string): void => {
    setListingType(listingType);
    onRefresh();
  };

  const onDeleteMedia = () => {
    toaster.warning(`Deleting ${mediaStore.length} items...`, {
      duration: 5,
      id: 'delete-toaster'
    });

    let promises: Promise<any>[] = [];

    movieStore.movies.forEach(movie => {
      movie.media.forEach(media => {
        if (media.id in mediaStore.media) {
          promises.push(
            mediaStore.deleteMedia(movie.key, media).then(() => {
              deletedMediaStore.addMedia(media);
            })
          )
        }
      });
    });

    Promise.all(promises).then(() => {
      toaster.success(`All items deleted!`, {
        duration: 5,
        id: 'delete-toaster'
      });

      setTimeout(() => {
        onRefresh();
      }, 4500);
    });
  };

  const onRefresh = () => {
    mediaStore.reset();
    deletedMediaStore.reset();
    if (listingType === 'duplicate') {
      movieStore.loadDupeMovies();
    } else if (listingType === 'sample') {
      movieStore.loadSampleMovies();
    }
  };

  const renderMovieList = () => (
    <Observer>
      {() => (
        <MovieList
          loading={movieStore.loading}
          loadingFailed={movieStore.loadingFailed}
          listingType={listingType}
          movies={movieStore.movies}
          renderMovieItem={renderMovieItem}
        />
      )}
    </Observer>
  );

  const renderMovieItem = (movie: Movie, key: number) => (
    <Observer key={key}>
      {() => (
        <MovieItem
          addMedia={(media: Media) => mediaStore.addMedia(media)}
          removeMedia={(media: Media) => mediaStore.removeMedia(media)}
          selectedMedia={mediaStore.media}
          deletedMedia={deletedMediaStore.media}
          movie={movie}
        />
      )}
    </Observer>
  );

  const renderTopPane = () => {
    return (
      <Observer>
        {() => (
          <MovieTopBar
            loading={movieStore.loading}
            deleting={mediaStore.length > 0 && deletedMediaStore.length > 0}
            numMovies={movieStore.length}
            numSelected={mediaStore.length}
            totalSize={bytesToSize(mediaStore.totalSizeBytes)}
            onDeleteMedia={onDeleteMedia}
            onRefresh={onRefresh}
            listingOptions={listingTypes}
            listingType={listingType}
            onListingTypeChange={onListingTypeChange}
          />
        )}
      </Observer>
    )
  };

  return (
    <Pane
      border="default"
      padding={majorScale(1)}
    >
      { renderTopPane() }
      { renderMovieList() }
    </Pane>
  )
};
