function runCounters() {
    const counters = document.querySelectorAll(".stat-counter");

    counters.forEach((counter) => {
        counter.innerHTML = 0;

        updateCounter = (counter) => {
            const isInt = counter.hasAttribute('data-counter-is-int');
            const target = parseFloat(counter.getAttribute('data-counter-target'));
            const current = parseFloat(counter.getAttribute('data-counter-current'));
            const increment = target / 200;

            if (current < target) {
                if (isInt) {
                    counter.innerHTML = `${Math.floor(current + increment).toLocaleString()}`;
                } else {
                    counter.innerHTML = `${(Math.round((current + increment) * 100) / 100).toLocaleString()}`;
                }

                counter.setAttribute('data-counter-current', current + increment);

                setTimeout(() => updateCounter(counter), 1)
            } else {
                counter.innerHTML = target.toLocaleString();
            }
        }

        updateCounter(counter);
    });
}

runCounters();