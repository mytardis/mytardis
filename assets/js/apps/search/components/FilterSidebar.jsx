import React from 'react'
import QuickSearchBox from './QuickSearchBox';
import FiltersSection from "./filters/filters-section/FiltersSection";
import './FilterSidebar.css';

export default function FilterSidebar() {
    return (
        <aside className="filter-sidebar">
            <QuickSearchBox  />
            <FiltersSection />
        </aside>
    )
}
