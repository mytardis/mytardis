import { combineReducers } from '@reduxjs/toolkit';

import search from './searchSlice';

const rootReducer = combineReducers({search});

export default rootReducer;