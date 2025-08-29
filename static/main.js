// ======== Inicializa o calendário ========
document.addEventListener('DOMContentLoaded', function() {
    const calendarEl = document.getElementById('calendar');

    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        locale: 'pt-br',
        height: 650,
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay,listWeek'
        },
        events: '/get_events', // rota Flask que retorna JSON dos agendamentos
        editable: false,
        selectable: true,
        select: function(info) {
            // Abre modal para adicionar agendamento
            const modal = new bootstrap.Modal(document.getElementById('modal-agendamento'));
            document.querySelector('#agendamento-data').value = info.startStr;
            modal.show();
        },
        eventClick: function(info) {
            alert('Evento: ' + info.event.title + '\nData: ' + info.event.start.toLocaleString());
        }
    });

    calendar.render();

    // ======== Adicionar Agendamento ========
    const formAgendamento = document.getElementById('form-agendamento');
    if(formAgendamento){
        formAgendamento.addEventListener('submit', async function(e) {
            e.preventDefault();
            const formData = new FormData(formAgendamento);
            const response = await fetch('/adicionar_agendamento', {
                method: 'POST',
                body: formData
            });
            const result = await response.json();
            if(result.success){
                alert('Agendamento adicionado com sucesso!');
                calendar.refetchEvents(); // atualiza o calendário
                formAgendamento.reset();
                bootstrap.Modal.getInstance(document.getElementById('modal-agendamento')).hide();
            } else {
                alert('Erro: ' + result.error);
            }
        });
    }

    // ======== Adicionar Cliente Dinâmico ========
    const formCliente = document.getElementById('form-cliente');
    if(formCliente){
        formCliente.addEventListener('submit', async function(e){
            e.preventDefault();
            const formData = new FormData(formCliente);
            const response = await fetch('/adicionar_cliente', {
                method: 'POST',
                body: formData
            });
            const result = await response.json();
            if(result.success){
                alert('Cliente adicionado com sucesso!');
                formCliente.reset();
                // Atualiza dropdown de clientes no modal de agendamento
                updateClienteDropdown(result.clientes);
            } else {
                alert('Erro: ' + result.error);
            }
        });
    }

    // ======== Função para atualizar dropdown de clientes ========
    function updateClienteDropdown(clientes){
        const select = document.getElementById('agendamento-cliente');
        if(!select) return;
        select.innerHTML = ''; // limpa opções
        clientes.forEach(c => {
            const option = document.createElement('option');
            option.value = c.id;
            option.textContent = c.nome;
            select.appendChild(option);
        });
    }

    // ======== Navegação entre páginas ========
    document.querySelectorAll('.nav-link.btn-nav').forEach(link => {
        link.addEventListener('click', function(e){
            // Navegação normal pelo Flask
            // Se quiser scroll interno, poderia usar:
            // e.preventDefault();
            // document.querySelector(this.getAttribute('href')).scrollIntoView({behavior: 'smooth'});
        });
    });
});
