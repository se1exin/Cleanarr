import {action, observable, runInAction} from 'mobx';
import React, {Context} from "react";
import {getDeletedSizes, getServerInfo} from "../util/api";

export class ServerInfoStore {
  @observable
  serverName = "";

  @observable
  serverUrl = "";

  @observable
  deletedSizes: Record<string, number> = {};

  @action
  loadServerInfo() {
    getServerInfo().then((result) => {
      runInAction(() => {
        this.serverName = result.data.name;
        this.serverUrl = result.data.url;
      })
    });
  }

  @action
  loadDeletedSizes() {
    return new Promise((resolve) => {
      getDeletedSizes().then((result) => {
        runInAction(() => {
          this.deletedSizes = result.data;
          resolve();
        })
      });
    });
  }
}

export function newServerInfoStore(): ServerInfoStore {
  return new ServerInfoStore();
}

export function newServerInfoStoreContext(): Context<ServerInfoStore> {
  return React.createContext<ServerInfoStore>(newServerInfoStore());
}

export const serverInfoContext = newServerInfoStoreContext();
