import {Alert, majorScale, Pane, Paragraph, Spinner} from "evergreen-ui";
import React, {FunctionComponent} from 'react';
import {Movie} from "../types";

type DupeMovieListProps = {
  loading: boolean,
  loadingFailed: boolean,
  loadingError: Error | null,
  listingType: string,
  movies: Movie[],
  renderMovieItem: (movie: Movie, key: number) => JSX.Element
}

export const MovieList:FunctionComponent<DupeMovieListProps> = (props) => {
  const {
    loading,
    loadingFailed,
    loadingError,
    listingType,
    movies,
    renderMovieItem
  } = props;

  const renderLoader = () => (
    <Pane
      display="flex"
      flexDirection={"column"}
      alignItems="center"
      background="tint2"
      borderRadius={3}
      padding={majorScale(2)}
      marginY={majorScale(1)}
    >
      { loadingFailed ?
        renderErrorAlert()
        :
        <>
          <Spinner size={30} flex={0}/>
          <Paragraph marginTop={majorScale(1)}>Loading...</Paragraph>
        </>
      }
    </Pane>
  );

  const renderErrorAlert = () => {
    return (
      <Alert
        intent="danger"
        title="Failed to load movies!"
      >
        {loadingError ? loadingError.message : 'Please check your Plex settings and try again.'}
      </Alert>
    )
  }

  const renderEmptyMessage = () => (
    <Pane
      display="flex"
      flexDirection={"column"}
      alignItems="center"
      background="tint2"
      borderRadius={3}
      padding={majorScale(2)}
      marginY={majorScale(1)}
    >
      <Alert
        intent="success"
        title={`No ${listingType} movies found`}
      />
    </Pane>
  );

  const renderMovieList = () => (
    <>
    {movies.map((movie: Movie, key: number) => (
        renderMovieItem(movie, key)
    ))}
    </>
  );


  return (
      <>
      { (loading || loadingFailed) ?
        renderLoader()
        : movies.length === 0 ?
          renderEmptyMessage()
        :
        renderMovieList()
      }
      </>
  )
};
