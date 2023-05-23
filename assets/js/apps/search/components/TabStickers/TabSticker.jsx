
import React from 'react';
import './TabSticker.css'

export default function TabSticker(props) {
    let backgroundColor = "#fafafa";
    const ORANGE = "#f7db8d";
    const BLUE = "#abe2ff";
    const PINK = "#ffcce8";
    const GREEN = "#70ffae";

    switch (props.initials) {
        case "P":
            backgroundColor = ORANGE;
            break;
        case "E":
            backgroundColor = BLUE;
            break;
        case "DS":
            backgroundColor = PINK;
            break;
        case "DF":
            backgroundColor = GREEN;
    }

    // TODO: add stickers that inherit from this base component
    // TODO: add size property support to change size.

    return (
        <div 
            className="tab-sticker"
            style={{backgroundColor: backgroundColor}}
        >
            <div className="tab-stick--content">
                {props.initials}
            </div>
        </div>
    )
}

export const ProjectTabSticker = () => {
    return (<TabSticker initials="P"></TabSticker>);
};

export const ExperimentTabSticker = () => {
    return (<TabSticker initials="E"></TabSticker>);
};

export const DatasetTabSticker = () => {
    return (<TabSticker initials="DS"></TabSticker>);
};

export const DatafileTabSticker = () => {
    return (<TabSticker initials="DF"></TabSticker>);
};

export const OBJECT_TYPE_STICKERS = {
    "project": ProjectTabSticker,
    "experiment": ExperimentTabSticker,
    "dataset": DatasetTabSticker,
    "datafile": DatafileTabSticker
}