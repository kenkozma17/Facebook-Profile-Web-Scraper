$(document).ready(function(){

    $('#example').DataTable( {
        "pagingType": "full_numbers"
    } );

    $.get("/process", function(data){
        pData = $.parseJSON(data);

         $( "#search" ).autocomplete({
            source: pData,
            select: function(event, ui){
                window.location.href = 'profile?id=' + ui.item.value;
            }

         });
    });

    $('#search').keyup(function(){

        $.ajax({
            data : {
                search : $('#search').val()
            },
            type : 'GET',
            url : '/process'
        })
        .done(function(data){

//            if(data.error) {
//                $('#errorAlert').text(data.error).show();
//                $('#successAlert').hide();
//            } else {
//                $('#successAlert').text(data.name).show();
//                $('#errorAlert').hide();
//            }

        });

        event.preventDefault();

    });
});
