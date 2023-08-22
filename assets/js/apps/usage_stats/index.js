function runCounters() {
    const counters = document.querySelectorAll(".stat-counter");

    counters.forEach((counter) => {
        console.log(counter);
        counter.innerHTML = 0;

        updateCounter = (counter) => {
            const target = parseFloat(counter.getAttribute('data-target'));
            const current = parseFloat(counter.getAttribute('data-current'));
            const increment = target / 200;
            
            if (current < target) {
                counter.innerHTML = `${Math.ceil(current + increment).toLocaleString()}`;
                counter.setAttribute('data-current', current + increment);

                setTimeout(() => updateCounter(counter), 1)
            } else {
                counter.innerHTML = target.toLocaleString();
            }
        }

        updateCounter(counter);
    });
}

runCounters();