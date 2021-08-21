import {action, observable, runInAction} from 'mobx';
import React, {Context} from "react";
import {getServerInfo} from "../util/api";

export class ServerInfoStore {
  @observable
  serverName = "";

  @observable
  serverUrl = "";

  @action
  loadServerInfo() {
    console.log('LOAD')
    getServerInfo().then((result) => {
      runInAction(() => {
        this.serverName = result.data.name;
        this.serverUrl = result.data.url;
      })
    });
  }
}

export function newServerInfoStore(): ServerInfoStore {
  return new ServerInfoStore();
}

export function newServerInfoStoreContext(): Context<ServerInfoStore> {
  return React.createContext<ServerInfoStore>(newServerInfoStore());
}
