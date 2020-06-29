
import React from 'react';
import './TabSticker.css'

export default function TabSticker(props) {
    let backgroundColor = "#fafafa";
    switch (props.initials) {
        case "P":
            backgroundColor = "#f7db8d";
            break;
        case "E":
            backgroundColor = "#abe2ff";
            break;
        case "DS":
            backgroundColor = "#ffcce8";
            break;
        case "DF":
            backgroundColor = "#70ffae";
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