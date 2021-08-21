import {Button, Card, Checkbox, Dialog, Heading, Icon, IconButton, Image, majorScale, Pane, Table} from "evergreen-ui";
import {Observer} from "mobx-react-lite";
import React, {FunctionComponent, useState} from 'react';
import {Media, MediaPart, Movie} from "../types";
import {bytesToSize, sumMediaSize} from "../util";
import {BACKEND_URL} from "../util/api";

type DupeMovieProps = {
  addMedia: Function,
  removeMedia: Function,
  onDeleteMedia: Function,
  selectedMedia: Record<number, Media>,
  deletedMedia: Record<number, Media>,
  movie: Movie
}

export const MovieItem:FunctionComponent<DupeMovieProps> = (props) => {

  const {
    addMedia,
    removeMedia,
    selectedMedia,
    deletedMedia,
    onDeleteMedia,
    movie
  } = props;


  const [mediaItemToDelete, setMediaItemToDelete] = useState<Media | null>(null);

  const onClickConfirmDelete = () => {
    onDeleteMedia(movie, mediaItemToDelete);
    setMediaItemToDelete(null);
  };

  const onCheckMedia = (media: Media, checked: boolean): void => {
    if (checked) {
      addMedia(media);
    } else {
      removeMedia(media);
    }
  };

  const onClickServerLink = () => {
    window.open(movie.url, '_blank');
  }

  return (
    <>
    <Card
      border="default"
      marginY={majorScale(1)}
    >
      <Pane
        padding={majorScale(1)}
        alignItems="center" display="flex"
      >
        <Image src={`${BACKEND_URL}server/proxy?url=${encodeURIComponent(movie.thumbUrl)}`} width={50} height={"auto"} marginRight={majorScale(2)} />
        <Pane flex={1}>
          <Heading>
            { `${movie.title} (${movie.year})` }
          </Heading>
          <Heading size={100}>
            { `${movie.library}` }
          </Heading>
        </Pane>
        <Button onClick={onClickServerLink}>
          Open in Plex
          <Icon icon={"share"} size={10} marginLeft={majorScale(1)} />
        </Button>
      </Pane>
      <Table>
        <Table.Head>
          <Table.TextHeaderCell flexBasis={50} flexShrink={0} flexGrow={0} />
          <Table.TextHeaderCell>File Size</Table.TextHeaderCell>
          <Table.TextHeaderCell>Video Size</Table.TextHeaderCell>
          <Table.TextHeaderCell>Resolution</Table.TextHeaderCell>
          <Table.TextHeaderCell>Frame Rate</Table.TextHeaderCell>
          <Table.TextHeaderCell>Codec</Table.TextHeaderCell>
          <Table.TextHeaderCell flexBasis={500}>Files</Table.TextHeaderCell>
          <Table.TextHeaderCell />
        </Table.Head>
        <Table.Body>
          {movie.media.map((media: Media, index: number) => (
            <Observer key={media.id}>
              {() => (
                <Table.Row
                  intent={media.id in deletedMedia ? 'danger' : 'none'}
                >
                  <Table.TextCell
                    flexBasis={50} flexShrink={0} flexGrow={0}
                  >
                    {media.id in deletedMedia ?
                      <Icon icon="cross" color="red" />
                      :
                      <Checkbox
                        label={""}
                        checked={(media.id in selectedMedia)}
                        disabled={(media.id in deletedMedia)}
                        onChange={e => onCheckMedia(media, e.target.checked)}
                      />
                    }
                  </Table.TextCell>
                  <Table.TextCell>
                    {bytesToSize(sumMediaSize(media))}
                  </Table.TextCell>
                  <Table.TextCell>
                    {(media.width) ? (`${media.width} x ${media.height}`) : '-'}
                  </Table.TextCell>
                  <Table.TextCell>{media.videoResolution}</Table.TextCell>
                  <Table.TextCell>{media.videoFrameRate}</Table.TextCell>
                  <Table.TextCell>{media.videoCodec}</Table.TextCell>
                  <Table.TextCell flexBasis={500}>
                    { media.parts.map((part: MediaPart, index: number) => (
                      <p style={{whiteSpace: "normal"}} key={index}>{ part.file }</p>
                    ))}
                  </Table.TextCell>
                  <Table.TextCell>
                    {!(media.id in deletedMedia) && (
                      <IconButton
                        appearance="primary"
                        intent="danger"
                        icon="trash"
                        disabled={mediaItemToDelete !== null && mediaItemToDelete.id === media.id}
                        onClick={() => setMediaItemToDelete(media)}
                      />
                    )}
                  </Table.TextCell>
                </Table.Row>
              )}
            </Observer>
          ))}
        </Table.Body>
      </Table>
    </Card>
        <Dialog
          isShown={mediaItemToDelete !== null}
          title="Warning"
          intent="danger"
          confirmLabel={`Delete Item`}
          onConfirm={onClickConfirmDelete}
          onCloseComplete={() => setMediaItemToDelete(null)}
        >
          Are you sure you want to delete the following file for <b>{movie.title}</b>?
          { mediaItemToDelete && mediaItemToDelete!.parts.map((part: MediaPart, index: number) => (
            <pre style={{whiteSpace: "normal"}} key={index}>{ part.file }</pre>
          ))}
        </Dialog>
    </>
  )
};
