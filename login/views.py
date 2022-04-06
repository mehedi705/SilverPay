from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, logout
from django.contrib.auth.models import User
from django.contrib.auth import login as access
from django.core.mail import send_mail
from datetime import date, datetime
from .models import balance_data, trans_data, key_pair1, key_pair2
import random


# Time Formatting for console
today = date.today()
now = datetime.now()
	
current_date = today.strftime("%d/%b/%Y")
current_time = now.strftime("%H:%M:%S")

this_moment = '[' + current_date + ' ' + current_time + ']'

# Protocols
def cash_in(request, amount):

    # SYSTEM --
    user = request.user
    user_current_balance = balance_data.objects.get(user=user)
    user_current_balance.total_amount = user_current_balance.total_amount + amount
    user_current_balance.save()
    return    
    

def cash_out(request, amount):

    # SYSTEM --
    user = request.user
    user_current_balance = balance_data.objects.get(user=user)
    user_current_balance.total_amount = user_current_balance.total_amount - amount
    user_current_balance.save()
    return

def initial_transaction(request, amount):
    user = request.user

    cash_in(request, amount)

    new_entry = trans_data(owner=user, total_amount = 1.0, des1 = 'Welcome Money', des2 = 'SilverPay provides some initial amount for every account', tr_amount = amount, in_out = 'in')
    new_entry.save()
    return

def send_money(request, the_username, amount):

    # SYSTEM --
    the_user = User.objects.get(username=the_username).pk
    user_current_balance = balance_data.objects.get(user= the_user)

    return HttpResponse(user_current_balance.total_amount)

''' ------------------------------------- Start BlockChain Protocol -------------------------------------------------'''
def coprime(a, b):
    while b != 0:
        a, b = b, a % b
    return a
    
    
def extended_gcd(aa, bb):
    lastremainder, remainder = abs(aa), abs(bb)
    x, lastx, y, lasty = 0, 1, 1, 0
    while remainder:
        lastremainder, (quotient, remainder) = remainder, divmod(lastremainder, remainder)
        x, lastx = lastx - quotient*x, x
        y, lasty = lasty - quotient*y, y
    return lastremainder, lastx * (-1 if aa < 0 else 1), lasty * (-1 if bb < 0 else 1)

# Euclid's extended algorithm for finding the multiplicative inverse of two numbers    
def modinv(a, m):
	g, x, y = extended_gcd(a, m)
	if g != 1:
		raise Exception('Modular inverse does not exist')
	return x % m    


def is_prime(num):
    if num == 2:
        return True
    if num < 2 or num % 2 == 0:
        return False
    for n in range(3, int(num**0.5)+2, 2):
        if num % n == 0:
            return False
    return True


def generate_keypair(p, q):
    if not (is_prime(p) and is_prime(q)):
        raise ValueError('Both numbers must be prime.')
    elif p == q:
        raise ValueError('p and q cannot be equal')

    n = p * q

    # Phi is the totient of n
    phi = (p-1) * (q-1)

    # Choose an integer e such that e and phi(n) are coprime
    e = random.randrange(1, phi)

    # Use Euclid's Algorithm to verify that e and phi(n) are comprime 
    g = coprime(e, phi)
  
    while g != 1:
        e = random.randrange(1, phi)
        g = coprime(e, phi)

    # Use Extended Euclid's Algorithm to generate the private key
    d = modinv(e, phi)

    # Return public and private keypair
    # Public key is (e, n) and private key is (d, n)
    return ((e, n), (d, n))


def primesInRange(x, y):
    prime_list = []
    for n in range(x, y):
        isPrime = True

        for num in range(2, n):
            if n % num == 0:
                isPrime = False
                
        if isPrime:
            prime_list.append(n)
    return prime_list



def generate_keys(request, username):

    the_user = User.objects.get(username=username).pk

    key1 = key_pair1.objects.get(user= the_user)
    key2 = key_pair2.objects.get(user= the_user)

    prime_list = primesInRange(17,2000)
    p = random.choice(prime_list)

    prime_list = primesInRange(2001,5000)
    q = random.choice(prime_list)

    # Generating publice and private key for the user
    print(this_moment + " Generating your public/private keypairs")
    public_key, private_key = generate_keypair(p, q) 

    public_key1, public_key2 = public_key
    private_key1, private_key2 = private_key
    
    key1.public_key = public_key1
    key1.private_key = private_key1

    key2.public_key = public_key2
    key2.private_key = private_key2

    key1.save()
    key2.save()

    return

'''------------------------------------- End BlockChain Protocol ----------------------------------------------------'''

# All Views

def login(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        print(this_moment + ' Fetch the login data')
        user = authenticate(username = username, password = password)
        if user is not None:
            print(this_moment + ' Sending to the kerberos authentication system')
            if user.is_active:
                access(request, user)
                print(this_moment + ' Authentication sucessful')
                return redirect('home')
        else:
            print(this_moment + ' Invalid authentication')
            return HttpResponse('Wrong username or password!')
        
    return render(request, 'login/logIn.html')


def OTP(request):
    if request.method == "POST":
        # OTP VALUE
        val1 = request.POST['val1']
        val2 = request.POST['val2']
        val3 = request.POST['val3']
        val4 = request.POST['val4']

        OTP_receive = str(val1) + str(val2) + str(val3) + str(val4)

        # SESSION VALUES
        username = request.session['username']
        email = request.session['email']
        passwd = request.session['passwd']
        OTP_actual = request.session['OTP']

        if(str(OTP_receive) == str(OTP_actual)):
            new_user = User.objects.create_user(username, email, passwd)

            new_user.save()

            del request.session['username']
            del request.session['email']
            del request.session['passwd']
            del request.session['OTP']

            user = authenticate(username = username, password = passwd)

            balance_data.objects.create(user=user)
            # trans_data.objects.create(user=user)
            key_pair1.objects.create(user=user)
            key_pair2.objects.create(user=user)

            
            if user is not None:
                if user.is_active:
                    access(request, user)
                    
                    # Generating kay pairs for new account
                    generate_keys(request, request.user.username)

                    # Given some initial amount from SilverPay
                    initial_transaction(request, 1000.0)

                    return redirect('home')
            else:
                return HttpResponse("Incorrect OTP!")

    return redirect('home')

def signup(request):
    if request.method == "POST":
        # RECEIVED VALUES
        username = request.POST['name']
        email = request.POST['email']
        pass1 = request.POST['pass1']
        pass2 = request.POST['pass2']

        # OTP GENERATOR
        OTP = random.randint(1000, 9999)
        actual_message = 'Your Registration OTP is : ' + str(OTP)
        
        # SESSION VALUES
        request.session['username'] = username
        request.session['email'] = email
        request.session['passwd'] = pass1
        request.session['OTP'] = OTP

        # Mailing PROTOCOL
        send_mail(
            'OTP From SilverPay Community' , # Subject
            actual_message, # Message
            email , # From Email
            [email], # To Email
        )

        return render(request, 'login/OTP.html')
        
    return render(request, 'login/SignUp.html')


def home(request):
    if request.user.is_authenticated:

        username = request.user.username
        context = {
            'username' : username,
            'transaction' : trans_data.objects.filter(owner=request.user.id).order_by("date").reverse(),
        }

        return render(request, 'profile/dashboard.html', context)
    else:
        return render(request, 'profile/index.html')

def transactions(request):
    if request.user.is_authenticated:

        username = request.user.username
        context = {
            'username' : username,
            'transaction' : trans_data.objects.filter(owner=request.user.id).order_by("date").reverse(),
        }
        return render(request, 'profile/transactions.html', context)
    else:
        return render(request, 'profile/index.html')


def send_money(request):
    if request.user.is_authenticated:
        return render(request, 'profile/send-money.html')
    else:
        return render(request, 'profile/index.html')

def req_money(request):
    if request.user.is_authenticated:
        return render(request, 'profile/request-money.html')
    else:
        return render(request, 'profile/index.html')
    

def profile(request):
    return render(request, 'profile/profile.html')

def profile_notifications(request):
    return render(request, 'profile/profile-notifications.html')

def signout(request):
    if request.user.is_authenticated:
        logout(request)
    return HttpResponse('Signout Successfull!')


