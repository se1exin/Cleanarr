import {Card, Checkbox, Heading, Icon, majorScale, Pane, Table} from "evergreen-ui";
import {Observer} from "mobx-react-lite";
import React, {FunctionComponent} from 'react';
import {Media, MediaPart, Movie} from "../types";
import {bytesToSize, sumMediaSize} from "../util";

type DupeMovieProps = {
  addMedia: Function,
  removeMedia: Function,
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
    movie
  } = props;

  const onCheckMedia = (media: Media, checked: boolean): void => {
    if (checked) {
      addMedia(media);
    } else {
      removeMedia(media);
    }
  };

  return (
    <Card
      border="default"
      marginY={majorScale(1)}
    >
      <Pane
        padding={majorScale(2)}
      >
        <Heading>
          { `${movie.title} (${movie.year})` }
        </Heading>
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
                </Table.Row>
              )}
            </Observer>
          ))}
        </Table.Body>
      </Table>
    </Card>
  )
};
