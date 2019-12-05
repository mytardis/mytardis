import React, {useState, useEffect, Fragment} from "react";

import  {Treebeard, decorators}  from 'react-treebeard';
import styles from './custom-theme';
import Header from './Header';
import Container from './Container';
import * as filters from './filter';

import Cookies from "js-cookie";
import PropTypes from "prop-types";


const TreeView = ({datasetId, modified}) => {

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
      const encodedDir = encodeURIComponent(dirName);
      const encodedData = encodeURIComponent(JSON.stringify(data));
      fetch(`/api/v1/dataset/${datasetId}/child-dirs/?dir_name=${encodedDir}&data=${encodedData}`,{
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
    },[datasetId, modified]);
    const onToggle = (node, toggled) => {
      //fetch children
      if (toggled && node.children && node.children.length === 0){
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
      let filtered_data = [];
      data.forEach(function(item) {
        let filtered = filters.filterTree(item, filter);
        filtered = filters.expandFilteredNodes(filtered, filter);
        filtered_data.push(filtered)
      });

      setData(filtered_data)
    };
    return (
      <Fragment>
        <div style={styles}>
          <div className="input-group">
              <span className="input-group-text">
                  <i className="fa fa-search"/>
              </span>
              <input
                  className="form-control"
                  onKeyUp={onFilterMouseUp}
                  placeholder="Search the tree..."
                  type="text"
              />
          </div>
        </div>
        <div style={styles}>
          <Treebeard
            data={data}
            style={styles}
            onToggle={onToggle}
            decorators={{...decorators, Header, Container}}
            animation={false}
          />
        </div>
      </Fragment>
    )
};

TreeView.propTypes = {
  datasetId: PropTypes.string.isRequired,
  modified: PropTypes.string,
};

TreeView.defaultProps = {
  modified: "",
};

export default TreeView;
