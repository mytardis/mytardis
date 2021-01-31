import React from 'react';
import { act } from '@testing-library/react';
import { configure, mount } from 'enzyme';
import Adapter from 'enzyme-adapter-react-16';
import fetchMock from 'jest-fetch-mock';
import TreeView from '../TreeView';


global.fetch = require('jest-fetch-mock');

configure({ adapter: new Adapter() });

const fakeTreeData = [{
  name: 'parent_1',
  path: 'parent_1',
  children: [],
},
{
  name: 'parent_2',
  path: 'parent_2',
  children: [],
},
{
  name: 'Parent.txt',
  id: 11985776,
  verified: true,
  is_online: true,
  recall_url: null,
},
{
  name: 'STORM-6.jpg',
  id: 11985840,
  verified: false,
  is_online: false,
  recall_url: '/api/v1/hsm_replica/1234/recall/',
},
{
  next_page: false,
},
];
const fakeChildData = [
  {
    name: 'child_1',
    path: 'parent_1/child_1',
    children: [],
  },
  {
    name: 'child_2',
    path: 'parent_1/child_2',
    children: [],
  },
  {
    name: 'Child_1.txt',
    id: 11985763,
    verified: true,
    is_online: true,
    recall_url: null,
  },
  {
    name: 'Child_2.txt',
    id: 11985764,
    verified: true,
    is_online: true,
    recall_url: null,
  }];


describe('should match snapshot', () => {
  let container = null;
  let component = null;
  beforeEach(async () => {
    jest.restoreAllMocks();
    fetch.resetMocks();
    fetchMock.mockResponseOnce(() => Promise.resolve(JSON.stringify(fakeTreeData)));
    container = document.createElement('div');
    document.body.appendChild(container);
    await act(async () => {
      component = mount(<TreeView datasetId="1234" modified="" />, { attachTo: container });
    });
    component.update();
  });
  afterEach(() => {
  // cleanup on exiting
    container.remove();
    container = null;
    component.unmount();
    component.detach();
    jest.restoreAllMocks();
    fetch.resetMocks();
  });
  it('should render folder tree correctly', async () => {
    expect(container).toMatchSnapshot();
  });
});
describe(' should render tree correctly', () => {
  let container = null;
  let component = null;
  beforeEach(async () => {
    jest.restoreAllMocks();
    fetchMock.mockClear();
    fetchMock.mockResponseOnce(() => Promise.resolve(JSON.stringify(fakeTreeData)));
    container = document.createElement('div');
    document.body.appendChild(container);
    await act(async () => {
      component = mount(<TreeView datasetId="1234" modified="" />, { attachTo: container });
    });
    component.update();
  });
  afterEach(() => {
  // cleanup on exiting
    container.remove();
    container = null;
    component.unmount();
    component.detach();
    jest.restoreAllMocks();
  });
  it('should render tree view with four child nodes', async () => {
    expect(container.querySelector('ul').children.length).toEqual(4);
    expect(container.querySelector('ul').children[0].textContent).toEqual('parent_1');
    expect(container.querySelector('ul').children[1].textContent).toEqual('parent_2');
    expect(container.querySelector('ul').children[2].textContent).toEqual('Parent.txt');
    expect(container.querySelector('ul').children[3].textContent).toEqual('STORM-6.jpg(unverified)');
  });
});
describe('test filter, select and toggle node', () => {
  let container = null;
  let component = null;
  beforeEach(async () => {
    jest.restoreAllMocks();
    fetchMock.mockClear();
    fetchMock.mockResponseOnce(() => Promise.resolve(JSON.stringify(fakeTreeData)));
    container = document.createElement('div');
    document.body.appendChild(container);
    await act(async () => {
      component = mount(<TreeView datasetId="1234" modified="" />, { attachTo: container });
    });
    component.update();
  });
  it('should render child nodes when clicked on parent', async () => {
    fetchMock.mockResponseOnce(() => Promise.resolve(JSON.stringify(fakeChildData)));
    // select folder before toggle
    await act(async () => {
      const checkBox = component.find({ type: 'checkbox' }).first();
      checkBox.simulate('click');
      setImmediate(() => {
        component.update();
        expect(component.find('Header').get(0).props.node.selected).toBeTruthy();
      });
    });
    // toggle folder open
    await act(async () => {
      component.find('NodeHeader').first().simulate('click');
    });
    component.update();
    expect(component.find('NodeHeader')).toHaveLength(8);
    expect(component.find('Header').get(0).props.iconClass).toEqual('folder-open');
    expect(component.find('Header').get(0).props.node.children.length).toEqual(4);
    expect(component.find('Header').get(0).props.node.children[0].name).toEqual('child_1');
    expect(component.find('TreeDownloadButton').get(0).props.count).toEqual(5);
    // toggle folder close
    await act(async () => {
      component.find('NodeHeader').first().simulate('click');
    });
    component.update();
    expect(component.find('NodeHeader')).toHaveLength(4);
    expect(component.find('Header').get(0).props.iconClass).toEqual('folder');
  });
  it('should filter tree node on search text change', async () => {
    fetchMock.mockResponseOnce(() => Promise.resolve(JSON.stringify(fakeChildData)));
    await act(async () => {
      component.find('NodeHeader').first().simulate('click');
    });
    await act(async () => {
      const searchField = component.find('input.form-control');
      searchField.simulate('keyUp', { target: { name: 'search-input', value: '2' } });
      // searchField.simulate('keyUp', { keyCode: 50 });
      setImmediate(() => {
        component.update();
        expect(component.find('NodeHeader')).toHaveLength(4);
      });
    });
  });
  it('should reload the tree if search text is empty', async () => {
    fetchMock.mockResponseOnce(() => Promise.resolve(JSON.stringify(fakeTreeData)));
    await act(async () => {
      const searchField = component.find('input.form-control');
      searchField.simulate('keyUp', { target: { name: 'search-input', value: '' } });
      setImmediate(() => {
        component.update();
        expect(component.find('NodeHeader')).toHaveLength(4);
        // should set count to 0
        expect(component.find('TreeDownloadButton').get(0).props.count).toEqual(0);
      });
    });
  });
  it('should deselect a selected node', async () => {
    const checkBox = component.find({ type: 'checkbox' }).first();
    checkBox.simulate('click');
    await act(async () => {
      checkBox.simulate('click');
    });
    component.update();
    expect(component.find('Header').get(0).props.node.selected).toBeFalsy();
  });
  it('should select all child nodes, if parent node is selected', async () => {
    expect(component.find('Header').get(0).props.node.selected).toBeFalsy();
    // select parent Node
    await act(async () => {
      const checkBox = component.find({ type: 'checkbox' }).first();
      checkBox.simulate('click');
    });
    component.update();
    expect(component.find('Header').get(0).props.node.selected).toBeTruthy();
    fetchMock.mockResponseOnce(() => Promise.resolve(JSON.stringify(fakeChildData)));
    await act(async () => {
      component.find('Container').first().simulate('click');
    });
    component.update();
    expect(component.find('NodeHeader')).toHaveLength(8);
    expect(component.find('Header').get(0).props.iconClass).toEqual('folder-open');
    expect(component.find('Header').get(1).props.node.selected).toBeTruthy();
    expect(component.find('Header').get(2).props.node.selected).toBeTruthy();
    component.update();
    expect(component.find('TreeDownloadButton').get(0).props.count).toEqual(5);
  });
  it('should deselect all child nodes, if parent node is deselected', async () => {
    fetchMock.mockResponseOnce(() => Promise.resolve(JSON.stringify(fakeChildData)));
    await act(async () => {
      component.find('Container').first().simulate('click');
    });
    component.update();
    await act(async () => {
      const checkBox = component.find({ type: 'checkbox' }).first();
      checkBox.simulate('click');
    });
    component.update();
    await act(async () => {
      const checkBox = component.find({ type: 'checkbox' }).first();
      checkBox.simulate('click');
    });
    component.update();
    expect(component.find('NodeHeader')).toHaveLength(8);
    expect(component.find('Header').get(1).props.node.selected).toBeFalsy();
    expect(component.find('Header').get(2).props.node.selected).toBeFalsy();
  });
  it('should select child node with no children', async () => {
    fetchMock.mockResponseOnce(() => Promise.resolve(JSON.stringify(fakeChildData)));
    await act(async () => {
      component.find('Container').first().simulate('click');
    });
    component.update();
    await act(async () => {
      const checkBox = component.find({ type: 'checkbox' }).at(6);
      checkBox.simulate('click');
    });
    component.update();
    expect(component.find('NodeHeader')).toHaveLength(8);
    expect(component.find('Header').get(6).props.node.selected).toBeTruthy();
  });
  it('should select all nodes when select All button is clicked', async () => {
    // find select all button
    await act(async () => {
      const selectAllButton = component.find('button').at(1);
      selectAllButton.simulate('click');
    });
    component.update();
  });
  it('should deselect all nodes when select None button is clicked', async () => {
    // find select all button
    await act(async () => {
      const selectAllButton = component.find('button').at(1);
      selectAllButton.simulate('click');
    });
    component.update();
    await act(async () => {
      const selectAllButton = component.find('button').at(1);
      selectAllButton.simulate('click');
    });
    component.update();
  });
});

describe('test download selected files', () => {
  let container = null;
  let component = null;
  beforeEach(async () => {
    jest.restoreAllMocks();
    fetchMock.mockClear();
    fetchMock.mockResponseOnce(() => Promise.resolve(JSON.stringify(fakeTreeData)));
    container = document.createElement('div');
    document.body.appendChild(container);
    await act(async () => {
      component = mount(<TreeView datasetId="1234" modified="" />, { attachTo: container });
    });
    component.update();
  });
  it('should download selected files', async () => {
    // select 2 files at root of the tree
    await act(async () => {
      const checkBox = component.find({ type: 'checkbox' }).at(2);
      checkBox.simulate('click');
    });
    component.update();
    // click on Download
    fetch.mockResponseOnce('[\'a\', \'b\', \'c\', \'d\']', {
      status: 200,
      headers: {
        'content-type': 'application/x-tar',
        'Content-Disposition': 'attachment; filename=manish-selection.tar',
        'Content-Length': '71680',
      },
    });
    jest.mock('file-saver', () => ({ saveAs: jest.fn() }));
    global.Blob = function f(content, options) { return ({ content, options }); };
    global.URL.createObjectURL = jest.fn();
    const downloadButton = component.find('form').simulate('submit');
    await act(async () => {
      downloadButton.simulate('click');
    });
    component.update();
    expect(fetch.mock.calls.length).toEqual(2);
    expect(fetch.mock.calls[1][1].body.get('comptype')).toEqual('tar');
    expect(fetch.mock.calls[1][1].body.get('organization')).toEqual('deep-storage');
    expect(fetch.mock.calls[1][1].body.getAll('datafile')).toEqual(['11985776']);
  });
  it('should download all files within a selected folder', async () => {
    // select Parent_1/child_1 folder
    fetchMock.mockResponseOnce(() => Promise.resolve(JSON.stringify(fakeChildData)));
    await act(async () => {
      const checkBox = component.find({ type: 'checkbox' }).first();
      checkBox.simulate('click');
      setImmediate(() => {
        component.update();
        expect(component.find('Header').get(0).props.node.selected).toBeTruthy();
      });
    });
    // toggle folder to load child component
    // toggle folder open
    await act(async () => {
      component.find('NodeHeader').first().simulate('click');
    });
    component.update();
    // eslint-disable-next-line global-require
    const utils = require('../Utils');
    utils.FetchFilesInDir = jest.fn(() => []);
    fetch.mockResponseOnce('[\'a\', \'b\', \'c\', \'d\']', {
      status: 200,
      headers: {
        'content-type': 'application/x-tar',
        'Content-Disposition': 'attachment; filename=manish-selection.tar',
        'Content-Length': '71680',
      },
    });
    jest.mock('file-saver', () => ({ saveAs: jest.fn() }));
    global.Blob = function f(content, options) { return ({ content, options }); };
    global.URL.createObjectURL = jest.fn();
    const downloadButton = component.find('form').simulate('submit');
    await act(async () => {
      downloadButton.simulate('click');
    });
    component.update();
    expect(fetch.mock.calls.length).toEqual(3);
    // expect download datafile endpoint is called
    expect(fetch.mock.calls['2'][0]).toEqual('/download/datafiles/');
    // expect methos to be POST
    expect(fetch.mock.calls['2'][1].method).toEqual('POST');
    // expect form data to include 3 datafile
    expect(fetch.mock.calls['2']['1'].body.getAll('datafile')).toEqual(['11985763', '11985764']);
  });
  it('should call api to get files in subdir', () => {
    jest.clearAllMocks().resetModules();
    // eslint-disable-next-line global-require
    const utils = require('../Utils');
    jest.spyOn(global, 'fetch').mockImplementation(() => Promise.resolve({
      json: () => Promise.resolve(12345),
    }));
    // eslint-disable-next-line no-unused-vars
    const response = utils.FetchFilesInDir('1234', 'Parent_1/');
    expect(fetch.mock.calls.length).toEqual(1);
    expect(fetch).toHaveBeenCalledWith('/api/v1/dataset/1234/child-dir-files/?dir_path=Parent_1/');
  });
});
