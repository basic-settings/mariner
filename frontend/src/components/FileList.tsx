import Avatar from "@material-ui/core/Avatar";
import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import IconButton from "@material-ui/core/IconButton";
import List from "@material-ui/core/List";
import ListItem from "@material-ui/core/ListItem";
import ListItemAvatar from "@material-ui/core/ListItemAvatar";
import ListItemSecondaryAction from "@material-ui/core/ListItemSecondaryAction";
import ListItemText from "@material-ui/core/ListItemText";
import LayersIcon from "@material-ui/icons/Layers";
import PrintIcon from "@material-ui/icons/Print";
import axios, { AxiosResponse } from "axios";
import nullthrows from "nullthrows";
import React from "react";

interface FileAPIResponse {
  filename: string;
}

function FileListItem({ file }: { file: FileAPIResponse }): React.ReactElement {
  return (
    <ListItem key={file.filename}>
      <ListItemAvatar>
        <Avatar>
          <LayersIcon />
        </Avatar>
      </ListItemAvatar>
      <ListItemText primary={file.filename} />
      <ListItemSecondaryAction>
        <IconButton edge="end" aria-label="print">
          <PrintIcon />
        </IconButton>
      </ListItemSecondaryAction>
    </ListItem>
  );
}

interface FileListAPIResponse {
  files: [FileAPIResponse];
}

export interface FileListState {
  isLoading: boolean;
  data?: FileListAPIResponse;
}

export default class FileList extends React.Component<{}, FileListState> {
  state: FileListState = {
    isLoading: true,
  };

  async componentDidMount(): Promise<void> {
    const response: AxiosResponse<FileListAPIResponse> = await axios.get(
      "api/list_files"
    );
    this.setState({
      isLoading: false,
      data: response.data,
    });
  }

  render(): React.ReactElement | null {
    if (this.state.isLoading) {
      return null;
    }

    const { files } = nullthrows(this.state.data);
    const listItems = files.map((file) => (
      <FileListItem file={file} key={file.filename} />
    ));

    return (
      <Card>
        <CardContent>
          <List>{listItems}</List>
        </CardContent>
      </Card>
    );
  }
}