import {Alert, majorScale, Pane, Paragraph, Spinner} from "evergreen-ui";
import React, {FunctionComponent} from 'react';
import {Content} from "../types";

type DupeMovieListProps = {
  loading: boolean,
  loadingFailed: boolean,
  loadingError: Error | null,
  listingType: string,
  content: Content[],
  renderContentItem: (movie: Content, key: number) => JSX.Element
}

export const ContentList:FunctionComponent<DupeMovieListProps> = (props) => {
  const {
    loading,
    loadingFailed,
    loadingError,
    listingType,
    content,
    renderContentItem
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
        title="Failed to load content!"
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
        title={`No ${listingType} content found`}
      />
    </Pane>
  );

  const renderMovieList = () => (
    <>
    {content.map((movie: Content, key: number) => (
        renderContentItem(movie, key)
    ))}
    </>
  );


  return (
      <>
      { (loading || loadingFailed) ?
        renderLoader()
        : content.length === 0 ?
          renderEmptyMessage()
        :
        renderMovieList()
      }
      </>
  )
};
