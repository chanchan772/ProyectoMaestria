/**
 * JavaScript principal del sitio
 */

// Smooth scroll para enlaces internos
document.addEventListener('DOMContentLoaded', function() {
    // Smooth scroll para enlaces con hash
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Activar tooltips de Bootstrap
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Animaciones al hacer scroll
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -100px 0px'
    };

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
            }
        });
    }, observerOptions);

    // Observar elementos con clase .fade-in
    document.querySelectorAll('.fade-in, .fade-in-delay').forEach(el => {
        observer.observe(el);
    });
});

// Función auxiliar para mostrar alertas
function showAlert(message, type = 'info') {
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;

    // Insertar alerta al principio del contenido principal
    const mainContent = document.querySelector('main');
    if (mainContent) {
        mainContent.insertAdjacentHTML('afterbegin', alertHtml);

        // Auto-cerrar después de 5 segundos
        setTimeout(() => {
            const alert = mainContent.querySelector('.alert');
            if (alert) {
                alert.remove();
            }
        }, 5000);
    }
}

// Función para formatear números
function formatNumber(num, decimals = 2) {
    if (num === null || num === undefined || isNaN(num)) {
        return 'N/A';
    }
    return parseFloat(num).toFixed(decimals);
}

// Función para formatear fechas
function formatDate(dateString) {
    const date = new Date(dateString);
    const options = {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    };
    return date.toLocaleDateString('es-CO', options);
}
