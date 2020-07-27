import { action } from '@storybook/addon-actions'

// Mock redux store for Storybook stories.
const makeMockStore = (state = {}) => {
    return {
        getState: () => {
            return state;
        },
        subscribe: () => 0,
        dispatch: action('dispatch'),
    };
}

export default makeMockStore;