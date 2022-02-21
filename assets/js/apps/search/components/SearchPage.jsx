import React, { useEffect } from 'react'
import './SearchPage.css'
import { initialiseSearch, restoreSearchFromHistory } from "./searchSlice";
import { useDispatch } from "react-redux";
import FilterSidebar from './FilterSidebar'
import ResultSection from './ResultSection'
import FilterSummaryBox from "./filter-summary/FilterSummaryBox";

export const SearchPage = () => {
    const dispatch = useDispatch();
    useEffect(() => {
        // Run a search to get initial results.
        dispatch(initialiseSearch());
    },[dispatch]);
    useEffect(() => {
        // Listen to navigation changes and redo searches.
        const redoSearch = (event) => {   
            dispatch(restoreSearchFromHistory(event.state));
        };
        window.addEventListener('popstate', redoSearch);
        return () => {
            window.removeEventListener('popstate',redoSearch)
        }
    },[dispatch]);
    return (
        <div className="search-page">
            <div className="search-screen">
                <aside className="filter-column" md={4}>
                    <FilterSidebar />
                </aside>
                <main className="result-column" md={8}>
                    <FilterSummaryBox />
                    <ResultSection />
                </main>
            </div>
        </div>
    )
}

export default SearchPage;