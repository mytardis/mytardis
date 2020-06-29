
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

    return (
        <div 
            className="tab-sticker"
            style={{'background-color': backgroundColor}}
        >
            <div className="content">
                {props.initials}
            </div>
        </div>
    )
}