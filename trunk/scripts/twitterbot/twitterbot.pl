use Irssi;
use Net::Twitter::Lite;
use vars qw($VERSION %IRSSI);

$VERSION = "1.0";
%IRSSI = (
    author => 'Xavier Garcia',
    contact => 'xavier\@shellguardians.com ',
    name => 'twitterbot',
    description => 'A bot to send tweets from an IRC channel',
    license => 'BSD License',
    url => 'http://www.shellguardians.com/'
);


sub twitter_msg {
  my ($nick,$msg,$channel,$server) = @_;
  my $allowed=0;
  my $nt = Net::Twitter::Lite->new(
    consumer_key    => $consumer_key,
    consumer_secret => $consumer_secret,
  );
  $nt->access_token($access_token);
  $nt->access_token_secret($access_token_secret);

  if ($server->{nick}!=$nick) {
     if (grep {$_ eq $nick} @access_list) {
         $allowed=1;
     }
  }
  else {
      $allowed=1;
  }
  if ($allowed) {
        eval { $nt->update("<$nick>: $msg") };
        if ( $@ ) {
             print "twitterbot: update failed because: $@\n";
        }
        print "twitterbot: <$nick>: $msg";
        $server->command("MSG $channel twitt sent.");
  }
  else {
      $server->command("MSG $channel $nick not authorized to twitt");
  }
}

sub sig_message_public {
     my ($server, $msg, $nick, $nick_addr, $channel) = @_;
     @data=split(" ",$msg);
     if ($channel=~ m/^$my_channel$/) { 
          if (@data[0]=~ m/^!twitt$/i) {
	       shift data;
               twitter_msg($nick,join(" ",@data),$channel,$server);
          }
     }
}

sub sig_message_own_public {
     my ($server, $msg, $channel) = @_;
     @data=split(" ",$msg);
     if ($channel=~ m/^$my_channel$/) {
          if (@data[0]=~ m/^!twitt/i) {
	       shift data;
               twitter_msg($server->{nick},join(" ",@data),$channel,$server);
          }
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
Irssi::signal_add 'message own_private', 'sig_message_own_public';

