import React, { useState, useEffect } from "react";
import ReactDOM from "react-dom";

import  { Treebeard }  from 'react-treebeard';
import styles from './components/custom-theme';
import decorators from 'react-treebeard/dist/components/decorators';

import Cookies from "js-cookie";


const tree_data = [
    {
      name: "Parent",
      children: [{ name: "child1" }, { name: "child2" }]
    },
    {
      name: "loading parent",
      loading: true,
      children: []
    },
    {
      name: "Parent",
      children: [
        {
          name: "Nested Parent",
          children: [{ name: "nested child 1" }, { name: "nested child 2" }]
        }
      ]
    }
];

const Container = ({ style, decorators, terminal, onClick, node}) => {
    const iconClass = node.children ? (node.toggled ? 'folder-open' : 'folder'): 'file-text';
    return(
      <div onClick={onClick}>
        <decorators.Header node={node} style={style.header} iconClass={iconClass}/>
      </div>
    ) ;
};

const Header = ({ node, style, iconClass }) => {
    const [iconTypeClass, setIconTypeClass] = useState(iconClass);
    const iconStyle = {marginRight: '5px'};

    return (
      <div style={style.base}>
        <div style={{ ...style.title }}>
            <i className={`fa fa-${iconTypeClass}`} style={iconStyle}/>
            {`${node.name}`}
        </div>
      </div>
    );

};


const TreeExample = ({datasetId}) => {

    const [cursor, setCursor] = useState(false);

    const [data, setData] = useState([]);
    const fetchData = (baseDir) => {
      fetch('/api/v1/dataset/'+datasetId+'/dirs/?base_dir='+baseDir+'&data='+JSON.stringify(data),{
        method: 'get',
        headers: {
            "Accept": "application/json", // eslint-disable-line quote-props
            "Content-Type": "application/json",
            "X-CSRFToken": Cookies.get("csrftoken"),
          },
      }).then(response => (response.json()))
        .then((data) => { setData(data)  })
    };
    useEffect(() => {fetchData('')},[]);
    const onToggle = (node, toggled) => {
      //fetch children
      console.log(node);
      if (toggled){
        fetchData(node.name);
      }
      console.log(node);
      if (cursor) {
          cursor.active = false;
      }
      node.active = true;
      if (node.children) {
          node.toggled = toggled;
      }
      setCursor(node);
      //setData(Object.assign([], data))
    };

    return (
          <Treebeard
            data={data}
            style={styles}
            onToggle={onToggle}
            decorators={{...decorators, Header, Container}}
            animation={false}
          />
    )
};
const content = document.getElementById('tree_view');
const href = window.location.href;
const datasetId = href.substring(href.lastIndexOf("/")+1);
ReactDOM.render(<TreeExample datasetId={datasetId}/>, content);
