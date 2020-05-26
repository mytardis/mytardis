import { createContext } from 'react';

const SearchInfoContext = createContext({
    searchTerm: null,
    isLoading: false,
    error:null,
    results:null,
    updateSearch: (query) => {}
});

export default SearchInfoContext;