#!/usr/bin/perl -w

#
# get_sig2.pl based on findimagedupes by Rob Kudla
#

# get_sig2.pl reads a set of lines of the format
# "<id><blank><filename>" from stdin and prints to stdout a set of
# lines in the format
# "<id><blank><image-signature>".
# <image-signature> is something like "34ef8a7c90713b"

use Image::Magick;

my $prog = $0 . '';
$prog = substr($prog,rindex($prog,'/') + 1) if rindex($prog,'/') >= 0;

# get imagemagick object
$image = Image::Magick->new;

while(<>)
{
    chomp;
    /^([^ ]+) (.*)$/;
    $hash=$1;
    $filename=$2;
    -e $filename or die "Can't find file '$filename'";

    $img = &getfingerprint($image, $filename);

    # only save if the image made a valid pbm.
    if (length($img) > 0) {
	print "$hash ";
	for ($i = 0; $i < length($img); $i++) {
	    # convert each byte of pbm to a hex pair.
	    print sprintf("%02x", ord(substr($img,$i,1)));
	}
	print "\n";
    }			
}

undef $image;

exit(0);

sub getfingerprint {

    #  here's a good a place as any to document the algorithm.  it's not
    #  so much an algorithm as a philosophy, it's kind of too lame to be
    #  an algorithm.  suggestions for improvement are very welcome.
	
    #  1. read file.
    #  2. standardize size by resampling to 160x160.
    #  3. grayscale it. (reducing saturation seems faster than quantize.)
    #  4. blur it a lot. (gets rid of noise.  we're going down 10x 
    #     more anyway) adding this nudges down false dupes about 
    #     10% and makes marginal dupes (e.g. big gamma difference) 
    #     show up about 10% higher.
    #  5. spread the intensity out as much as possible (normalize.)
    #  6. make it as contrasty as possible (equalize.)
    #     this is for those real dark pictures that someone has slapped
    #     a pure white logo on.  yes, i tested this thoroughly on pr0n!
    #  7. resample again down to 16x16.  I wanted to use a mosaic/pixelate
    #     kind of thing but hopefully imagemagick's resample function works
    #     roughly the same way.
    #  8. reduce to 1bpp (threshold using defaults)
    #  9. convert to pbm
    #  10. save out to database as hex string containing raw pbm data
    #  11. when comparing, xor each file pair's pbm strings.
    #  12. count the 1 bits in the result to approximate similarity.

    my $image = shift;
    my $file = shift;
    my (@blobs, $img);
	
    $x = $image->Read($file);
    die "ERROR: $x" if "$x"; 
    $#$image = 0;
    $x = $image->Sample("160x160!");
    die "ERROR: $x" if "$x"; 
    $x = $image->Modulate(saturation=>-100);
    die "ERROR: $x" if "$x"; 
    #$x = $image->Blur(factor=>99);
    $x = $image->Blur(radius=>15, sigma=>19);
    die "ERROR: $x" if "$x"; 
    $x = $image->Normalize();
    die "ERROR: $x" if "$x"; 
    $x = $image->Equalize();
    die "ERROR: $x" if "$x"; 
    $x = $image->Sample("16x16");
    die "ERROR: $x" if "$x"; 
    $x = $image->Threshold();
    die "ERROR: $x" if "$x"; 
    $x = $image->Set(magick=>'pbm');
    die "ERROR: $x" if "$x"; 
    @blobs = $image->ImageToBlob();
    die "ERROR: $x" if "$x"; 
    $img = substr($blobs[0],-32,32);

    # free image but don't delete object.
    undef @$image;

    $img;
}
