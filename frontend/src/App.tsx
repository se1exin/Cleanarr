import {Badge, Button, Heading, Icon, majorScale, Pane} from 'evergreen-ui'
import {Observer} from "mobx-react-lite";
import React, {useEffect} from 'react';
import './App.css';
import {ContentPage} from "./components/ContentPage";
import {serverInfoContext} from "./stores/ServerInfoStore";
import {bytesToSize} from "./util";

const App = () => {

  const serverInfoStore = React.useContext(serverInfoContext);

  useEffect(() => {
    serverInfoStore.loadServerInfo();
    serverInfoStore.loadDeletedSizes();
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
        justifyContent={"center"}
      >
        <Pane flex={1}>
          <Heading >
            Cleanarr
          </Heading>
        </Pane>

        <Observer>
          {() => (
            <Pane display="flex" alignItems="center" justifyContent={"center"}>
              <Pane marginRight={20}>
                <Badge color="blue">
                  Lifetime Space Saved:
                  {Object.keys(serverInfoStore.deletedSizes).map((key) => {
                    return (
                      <span className={"deleted-size"} key={key}>{key}: {bytesToSize(serverInfoStore.deletedSizes[key])}</span>
                    )
                  })}
                </Badge>
              </Pane>
            </Pane>
          )}
        </Observer>

        <Observer>
          {() => (
            <>
              {serverInfoStore.serverUrl && (
                <Button onClick={onClickServerLink}>
                  {serverInfoStore.serverName}
                  <Icon icon={"share"} size={10} marginLeft={majorScale(1)} />
                </Button>
              )}
            </>
          )}
        </Observer>

      </Pane>
      <ContentPage />
    </Pane>
  );
}

export default App;
