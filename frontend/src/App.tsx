import {Heading, majorScale, Pane} from 'evergreen-ui'
import React from 'react';
import './App.css';
import {MoviePage} from "./components/MoviePage";

class App extends React.Component<any, any> {

  render() {
    return (
      <Pane>
        <Pane
          background="tint2"
          borderRadius={0}
          elevation={1}
          border="muted"
          padding={majorScale(2)}
        >
          <Heading>Plex Library Cleaner</Heading>
        </Pane>
        <MoviePage/>
      </Pane>
    );
  }
}

export default App;
