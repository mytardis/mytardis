import React, {useState, useEffect, Fragment} from "react";
import ReactDOM from "react-dom";

import  { Treebeard }  from 'react-treebeard';
import styles from './components/custom-theme';
import decorators from 'react-treebeard/dist/components/decorators';
import { Div } from 'react-treebeard/dist/components/common';
import * as filters from './components/filter'

import Cookies from "js-cookie";

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
            {node.name}
        </div>
      </div>
    );

};


const TreeExample = ({datasetId}) => {

    const [cursor, setCursor] = useState(false);
    const [baseData, setBaseData] = useState([]);
    const [data, setData] = useState([]);
    const fetchBaseDirs = () => {
      fetch('/api/v1/dataset/'+datasetId+'/base-dirs/',{
        method: 'get',
        headers: {
            "Accept": "application/json", // eslint-disable-line quote-props
            "Content-Type": "application/json",
            "X-CSRFToken": Cookies.get("csrftoken"),
          },
      }).then(response => (response.json()))
        .then((data) => { setBaseData(data); setData(data)  })
    };
    const fetchChildDirs = (dirName) => {
      fetch('/api/v1/dataset/'+datasetId+'/child-dirs/?dir_name='+dirName+'&data='+JSON.stringify(data),{
        method: 'get',
        headers: {
            "Accept": "application/json", // eslint-disable-line quote-props
            "Content-Type": "application/json",
            "X-CSRFToken": Cookies.get("csrftoken"),
          },
      }).then(response => (response.json()))
        .then((data) => { setData(data)  })
    };
    useEffect(() => {
      fetchBaseDirs('')
    },[]);
    const onToggle = (node, toggled) => {
      //fetch children
      if (toggled && node.children.length === 0){
        fetchChildDirs(node.name);
      }else {
        node.toggled = toggled;
      }
      if (cursor) {
          cursor.active = false;
      }
      node.active = true;
      if (node.children) {
          node.toggled = toggled;
      }
      setCursor(node);
      setData(Object.assign([], data))
    };
    const onFilterMouseUp = ({target: {value}}) => {
      const filter = value.trim();
      if (!filter) {
        //return initial tree state
        return fetchBaseDirs('');
      }
      let filtered_data = []
      data.forEach(function(item) {
        let filtered = filters.filterTree(item, filter);
        filtered = filters.expandFilteredNodes(filtered, filter);
        filtered_data.push(filtered)
      });

      setData(filtered_data)
    };
    return (
      <Fragment>
        <Div style={styles.searchBox}>
          <Div className="input-group">
              <span className="input-group-addon">
                  <i className="fa fa-search"/>
              </span>
              <input
                  className="form-control"
                  onKeyUp={onFilterMouseUp}
                  placeholder="Search the tree..."
                  type="text"
              />
          </Div>
        </Div>
        <Div style={styles}>
          <Treebeard
            data={data}
            style={styles}
            onToggle={onToggle}
            decorators={{...decorators, Header, Container}}
            animation={false}
          />
        </Div>
      </Fragment>

    )
};
const content = document.getElementById('tree_view');
const href = window.location.href;
const datasetId = href.substring(href.lastIndexOf("/")+1);
ReactDOM.render(<TreeExample datasetId={datasetId}/>, content);
