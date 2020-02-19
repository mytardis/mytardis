import React from 'react';
import ReactDOM from 'react-dom';
import { act } from '@testing-library/react';
import { configure, mount } from 'enzyme';
import Adapter from 'enzyme-adapter-react-16';
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
},
{
  name: 'STORM-6.jpg',
  id: 11985840,
}];
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
  },
  {
    name: 'Child_2.txt',
    id: 11985764,
  }];

let container = null;
let component = null;
beforeEach(async () => {
  jest.spyOn(global, 'fetch').mockImplementation(() => Promise.resolve({
    json: () => Promise.resolve(fakeTreeData),
  }));
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
});

describe('renders initial tree view on page load', () => {
  it('should render folder tree correctly', async () => {
    await act(async () => {
      ReactDOM.render(<TreeView datasetId="1234" modified="" />, container);
    });
    expect(container).toMatchSnapshot();
  });
  it('should render tree view with four child nodes', async () => {
    await act(async () => {
      ReactDOM.render(<TreeView datasetId="1234" modified="" />, container);
    });
    expect(container.querySelector('ul').children.length).toEqual(4);
    expect(container.querySelector('ul').children[0].textContent).toEqual('parent_1');
    expect(container.querySelector('ul').children[1].textContent).toEqual('parent_2');
    expect(container.querySelector('ul').children[2].textContent).toEqual('Parent.txt');
    expect(container.querySelector('ul').children[3].textContent).toEqual('STORM-6.jpg');
  });
});

describe('test filter, select and toggle node', () => {
  afterAll(() => {
    component.unmount();
    component.detach();
    component.update();
  });
  it('should render child nodes when clicked on parent', async () => {
    jest.spyOn(global, 'fetch').mockImplementation(() => Promise.resolve({
      json: () => Promise.resolve(fakeChildData),
    }));
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
    await act(async () => {
      const searchField = component.find('input.form-control');
      searchField.simulate('keyUp', { target: { name: 'search-input', value: '2' } });
      // searchField.simulate('keyUp', { keyCode: 50 });
      setImmediate(() => {
        component.update();
        expect(component.find('NodeHeader')).toHaveLength(6);
      });
    });
  });
  it('should reload the tree if search text is empty', async () => {
    jest.spyOn(global, 'fetch').mockImplementation(() => Promise.resolve({
      json: () => Promise.resolve(fakeTreeData),
    }));
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
  it('should deselect a node', async () => {
    await act(async () => {
      const checkBox = component.find({ type: 'checkbox' }).first();
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
    jest.spyOn(global, 'fetch').mockImplementation(() => Promise.resolve({
      json: () => Promise.resolve(fakeChildData),
    }));
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
  it('should deselect folder nodes', async () => {
    expect(component.find('Header').get(1).props.node.selected).toBeTruthy();
    await act(async () => {
      const checkBox = component.find({ type: 'checkbox' }).at(1);
      checkBox.simulate('click');
    });
    component.update();
    expect(component.find('NodeHeader')).toHaveLength(8);
    expect(component.find('Header').get(1).props.node.selected).toBeFalsy();
  });
  it('should select  a folder nodes', async () => {
    expect(component.find('Header').get(1).props.node.selected).toBeFalsy();
    await act(async () => {
      const checkBox = component.find({ type: 'checkbox' }).at(1);
      checkBox.simulate('click');
    });
    component.update();
    expect(component.find('NodeHeader')).toHaveLength(8);
    expect(component.find('Header').get(1).props.node.selected).toBeTruthy();
  });
  it('should deselect all child nodes, if parent node is deselected', async () => {
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
    await act(async () => {
      const checkBox = component.find({ type: 'checkbox' }).last();
      checkBox.simulate('click');
    });
    component.update();
    expect(component.find('NodeHeader')).toHaveLength(8);
    expect(component.find('Header').get(7).props.node.selected).toBeTruthy();
  });
  it('should deselect child node with no children', async () => {
    expect(component.find('Header').get(7).props.node.selected).toBeTruthy();
    await act(async () => {
      const checkBox = component.find({ type: 'checkbox' }).last();
      checkBox.simulate('click');
    });
    component.update();
    expect(component.find('NodeHeader')).toHaveLength(8);
    expect(component.find('Header').get(7).props.node.selected).toBeFalsy();
  });
});

describe('test download selected files', () => {
  it('should download selected files', async () => {
    // select 2 files at root of the tree
    await act(async () => {
      const checkBox = component.find({ type: 'checkbox' }).at(7);
      checkBox.simulate('click');
    });
    component.update();
    await act(async () => {
      const checkBox = component.find({ type: 'checkbox' }).at(6);
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
  });
});
