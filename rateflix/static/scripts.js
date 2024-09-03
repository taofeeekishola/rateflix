$(document).ready(function(){
    $('.movies').click(function(){
        //to indicate if the movie is in your checklist or not
        var bttn = $(this).hasClass('btn-outline-primary');

        if(bttn == true){
            $(this).removeClass('btn-outline-primary')
            $(this).addClass('btn-primary')
            $(this).html('<i class="fa-solid fa-check"></i> Added')
        }else if(bttn == false){
            $(this).removeClass('btn-primary')
            $(this).addClass('btn-outline-primary')
            $(this).html('<i class="fa-solid fa-plus"></i> Watchlist')
        }
        });

    $('.added').click(function(){
        var bttn2 = $(this).hasClass('btn-primary');

        if(bttn2 == true){
             $(this).removeClass('btn-primary')
            $(this).addClass('btn-outline-primary')
            $(this).html('<i class="fa-solid fa-plus"></i> Watchlist')
        }else if(bttn2 == false){
            $(this).removeClass('btn-outline-primary')
            $(this).addClass('btn-primary')
            $(this).html('<i class="fa-solid fa-check"></i> Added')
        }
    });

    //to comment on a movie
    $('.comment').click(function(){
       var comment = $('.movieComment').val()
        $('.mycomment').html(comment);
        $('.movieComment').val('')
    });

   $('.login').click(function(event){
        event.preventDefault(); // Prevent form submission

        var username = $('#floatingInput').val();
        var pwd = $('#floatingPassword').val();

        if(username === '' || pwd === ''){
            $('.alert').html('Please enter your full details').show(); // Show the alert
        } else {
            $('.alert').hide(); // Hide the alert if details are entered
            $('#loginForm').submit(); // Manually submit the form
        }
    });
});