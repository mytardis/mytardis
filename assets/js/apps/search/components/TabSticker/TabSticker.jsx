
import React from 'react';
import './TabSticker.css'

export default function TabSticker(props) {
    return (
        <div className="tab-sticker">
            <div className="content">
                {props.initials}
            </div>
        </div>
    )
}