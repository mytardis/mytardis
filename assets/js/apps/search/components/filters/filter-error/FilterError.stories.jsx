import React from 'react'
import FilterError from './FilterError';
import { action } from '@storybook/addon-actions';

export default {
    component: FilterError,
    title: 'Filter Error Popup',
    decorators: [story => <div style={{ padding: '3rem', width: "300px" }}>{story()}</div>],
    excludeStories: /.*Data$/,
};

const message = {
    numberRange: 'Invalid Range Values',
    dateRange: 'Invalid Date Range'
};

export const NumberRange = () => (
    <FilterError message={message.numberRange} />
)

export const DateRange = () => (
    <FilterError message={message.dateRange} />
)

const Template = (args) => <FilterError {...args} />;

export const Default = Template.bind({});
Default.args = {
    message: "message",
    longMessage: "longer message",
    showIcon: false
};

export const CustomMessages = Template.bind({});
CustomMessages.args = {
    message: 'custom short message',
    longMessage: 'custom long message',
    showIcon: false
};

export const WithLabel = Template.bind({})
WithLabel.args = {
    message: 'custom short message',
    longMessage: 'custom tooltip',
    showIcon: true
};