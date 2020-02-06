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

describe('renders initial tree view on page load', () => {
  let container = null;
  beforeEach(() => {
    jest.spyOn(global, 'fetch').mockImplementation(() => Promise.resolve({
      json: () => Promise.resolve(fakeTreeData),
    }));
    container = document.createElement('div');
    document.body.appendChild(container);
  });
  afterEach(() => {
    // cleanup on exiting
    container.remove();
    container = null;
  });
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

describe('test rendering child nodes and filter', () => {
  let component = null;
  beforeEach(async () => {
    jest.spyOn(global, 'fetch').mockImplementation(() => Promise.resolve({
      json: () => Promise.resolve(fakeTreeData),
    }));
    await act(async () => {
      component = mount(<TreeView datasetId="1234" modified="" />);
    });
    component.update();
  });
  it('should render child nodes when clicked on parent', async () => {
    jest.spyOn(global, 'fetch').mockImplementation(() => Promise.resolve({
      json: () => Promise.resolve(fakeChildData),
    }));
    await act(async () => {
      component.find('NodeHeader').first().simulate('click');
    });
    component.update();
    expect(component.find('NodeHeader')).toHaveLength(8);
    expect(component.find('Header').get(0).props.iconClass).toEqual('folder-open');
    expect(component.find('Header').get(0).props.node.children.length).toEqual(4);
    expect(component.find('Header').get(0).props.node.children[0].name).toEqual('child_1');
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
});
