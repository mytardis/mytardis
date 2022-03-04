import initStoryshots from '@storybook/addon-storyshots';

// Set date to be constant so snapshots are consistent. This is because Datetime picker as used in DateRangeFilter
// changes its output based on today's date.

Date.now = jest.fn(() => 1606693372520);

// Generate snapshot tests for stories. This ensures components
// as rendered in the storybook stay consistent unless we want
// to change them.
// Read more in https://github.com/storybookjs/storybook/tree/master/addons/storyshots/storyshots-core
initStoryshots();