use Irssi;
use Net::Twitter::Lite;
use Encode;
use HTML::FormatText;
use vars qw($VERSION %IRSSI);

$VERSION = "1.0";
%IRSSI = (
    author => 'Xavier Garcia',
    contact => 'xavier\@shellguardians.com ',
    name => 'twitterbot',
    description => 'A bot to send twits from an IRC channel',
    license => 'BSD License',
    url => 'http://www.shellguardians.com/'
);


sub load_tokens {
  my $nt = Net::Twitter::Lite->new(
    consumer_key    => $consumer_key,
    consumer_secret => $consumer_secret,
  );
  $nt->access_token($access_token);
  $nt->access_token_secret($access_token_secret);
  return $nt;
}
sub twitter_msg {
  my ($nick,$msg,$channel,$server) = @_;
  my $allowed=0;
  my $nt = load_tokens();
  if ($server->{nick}!=$nick) {
     if (grep {$_ eq $nick} @access_list) {
         $allowed=1;
     }
  }
  else {
      $allowed=1;
  }
  if ($allowed) {
        if (length($msg) <= 120) {
            eval { $nt->update("<$nick>: $msg") };
            if ( $@ ) {
                 print "twitterbot: update failed because: $@\n";
            }
            $server->command("MSG $channel twit sent.");
        }
	else {
            $server->command("MSG $channel The message is longer than 120 characters.");
        }
  }
  else {
      $server->command("MSG $channel $nick not authorized to twit");
  }
}

sub sig_message_public {
     my ($server, $msg, $nick, $nick_addr, $channel) = @_;
     manage_cmd($server,$msg,$channel,$nick);
}

sub sig_message_own_public {
     my ($server, $msg, $channel) = @_;
     manage_cmd($server,$msg,$channel,$server->{nick});
}


sub manage_cmd {
    my ($server,$msg,$channel,$nick) = @_;
    @data=split(" ",$msg);
    if ($channel=~ m/^$my_channel$/) { 
         if (@data[0]=~ m/^!twitt$/i) {
              shift data;
              twitter_msg($nick,join(" ",@data),$channel,$server);
         }
         elsif(@data[0]=~ m/^!twitstatus$/i) {
             check_timeline($nick,$server);
         }
    }
}

sub check_timeline {
    my ($nick, $server) = @_;
    my $nt = load_tokens();

    my $timeline = $nt->home_timeline({ count => 10 });
    my @results = ();
    for my $tweet ( @$timeline ) {
        my @item = ();
        if ( $tweet->{retweeted_status} ) {
            @item = ( encode_utf8($tweet->{user}{screen_name}) ,
                encode_utf8($tweet->{retweeted_status}{text}) ,
                encode_utf8($tweet->{retweeted_status}{created_at}));
        } else {
            @item = ( encode_utf8($tweet->{user}{screen_name}) ,
                encode_utf8($tweet->{text}) ,
                encode_utf8($tweet->{created_at}));
        }
        push @results, \@item;
    }

    foreach (@results) {
        my @result;
        my @array=$_;
        my $name=$array[0][0];
        my $text=$array[0][1];
        my $date=$array[0][2];

        my $plaintext= HTML::FormatText->format_string(
            $text,leftmargin => 0, rightmargin => 200);
      
        $twit= "$date  $name : $plaintext";
        chomp($twit);
        push @result, $twit;
        $server->command("MSG $nick " . join("\n",@result));
   }
}


$my_channel="#mychannel";
@access_list = ("nick1","nick2");
$consumer_key="CUSTOMER_KEY";
$consumer_secret="CUSTOMER_SECRET_KEY";
$access_token="ACCESS_TOKEN";
$access_token_secret="ACCESS_TOKEN_SECRET";

Irssi::signal_add 'message public', 'sig_message_public';
Irssi::signal_add 'message own_public', 'sig_message_own_public';
