import React from 'react'
import { configure } from 'enzyme';
import Adapter from 'enzyme-adapter-react-16';
import Search from './components/Search'
import Result from './components/Result'
import { shallow } from 'enzyme'
configure({ adapter: new Adapter() });
const result = {
  title: "Test Group - Test Experiment 1",
  description: "Uploader: Test Instrument",
  type: "experiment",
  id: '8369',
  url: "/experiment/view/8369/",
};

describe('Search Component', () => {
  it('Render Search Component',() => {
    const search = shallow(<Search/>);
    expect(search.exists()).toBeTruthy()
  })

});

describe('Result Component', () => {
  it('Test Result component',() => {
    const wrapper = shallow(<Result key={result.id} result={result} />);
    expect(wrapper.exists()).toBeTruthy()
  })

});