import {Button, Heading, Icon, majorScale, Pane} from 'evergreen-ui'
import {Observer} from "mobx-react-lite";
import React, {useEffect} from 'react';
import './App.css';
import {MoviePage} from "./components/MoviePage";
import {newServerInfoStoreContext} from "./stores/ServerInfoStore";

const App = () => {

  const serverInfoStore = React.useContext(newServerInfoStoreContext());

  useEffect(() => {
    serverInfoStore.loadServerInfo();
  });

  const onClickServerLink = () => {
    window.open(serverInfoStore.serverUrl, '_blank');
  }

  return (
    <Pane>
      <Pane
        background="tint2"
        borderRadius={0}
        elevation={1}
        border="muted"
        padding={majorScale(2)}
        display={"flex"}
        alignItems={"center"}
      >
        <Pane flex={1}>
          <Heading >
            Plex Library Cleaner
          </Heading>
        </Pane>

          <Observer>
            {() => (
              <>
                {serverInfoStore.serverUrl && (
                  <Button onClick={onClickServerLink}>
                    {serverInfoStore.serverName}
                    <Icon icon={"share"} size={10} style={{marginLeft: "5px"}} />
                  </Button>
                )}
              </>
            )}
          </Observer>

      </Pane>
      <MoviePage/>
    </Pane>
  );
}

export default App;
